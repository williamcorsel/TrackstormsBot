import argparse
import logging

import cv2
from flask import Flask, Response, render_template

from trackstormsbot.camera import CameraStream
from trackstormsbot.controller import DistanceSensorController, MotorController
from trackstormsbot.detectors import *
from trackstormsbot.gesture_recognisers import *
from trackstormsbot.utils import *

log = logging.getLogger(__name__)

app = Flask(__name__, template_folder='trackstormsbot/templates')

DETECTOR_MAP = {
    'haarcascade': CascadeDetector,
    'yunet': YuNetDetector,
    'mediapipe': MediapipeDetector,}


def get_args():
    parser = argparse.ArgumentParser('Trackstormsbot')
    parser.add_argument('-c', '--camera', type=int, default=0, help='Camera index')
    parser.add_argument('-d',
                        '--detector',
                        type=str,
                        default='yunet',
                        choices=DETECTOR_MAP.keys(),
                        help='Name of detector model to use')
    parser.add_argument('--motor_ports', type=str, nargs=2, default=['A', 'B'], help='Motor Ports (X-axis, Y-axis)')
    parser.add_argument('--distance_port', type=str, default='C', help='Distance Sensor Port')
    parser.add_argument('--disable_controller', action='store_true', help='Disable controller')
    parser.add_argument('--detector_rate', type=int, default=30, help='Detector rate (FPS)')
    parser.add_argument('--gesture_rate', type=int, default=30, help='Gesture recogniser rate (FPS)')
    return parser.parse_args()


def get_detector(detector_name, camera, rate, **kwargs):
    detector_class = DETECTOR_MAP[detector_name]
    return detector_class(camera, rate, **kwargs)


def video_stream():
    args = get_args()

    camera = CameraStream(args.camera)
    detector = get_detector(args.detector, camera, args.detector_rate)
    gesture_recogniser = MediapipeRecogniser(camera, args.gesture_rate)
    controller = MotorController(args.motor_ports)
    distance_sensor = DistanceSensorController(args.distance_port)

    camera.open()
    gesture_recogniser.start()
    detector.start()

    frame_size = camera.size()
    frame_middle = (frame_size[0] // 2, frame_size[1] // 2)

    while (camera.is_opened()):
        frame = camera.read()

        if frame is None:
            continue

        detections, _ = detector.read()
        gesture_detections, gesture = gesture_recogniser.read()

        if len(detections) > 0:
            detection = detections[0]
        else:
            detection = None

        frame_vis = camera.read()

        if not args.disable_controller:
            if detection is not None:
                relative_size = detection[2] * detection[3] / (frame_size[0] * frame_size[1])
                middle = calculate_middle_xywh(detection)
                frame_vis = visualise_detection(frame_vis, detection)
                frame_vis = visualise_landmarks(frame_vis, gesture_detections)
                controller.move_to_middle(
                    frame_middle=frame_middle,
                    detection_middle=middle,
                    detection_size=relative_size,
                )
            else:
                controller.stop()

        if gesture == 'point':
            distance_sensor.set_eyes(100, 100, 100, 100)
        else:
            distance_sensor.set_eyes(0, 0, 0, 0)

        stats = {
            'FPS (Camera)': int(camera.fps()),
            'FPS (Detector)': int(detector.fps()),
            'FPS (Gesture)': int(gesture_recogniser.fps()),
            'Distance (cm)': distance_sensor.get_distance(),
            'Gesture': gesture,}

        frame_vis = visualise_stats(frame_vis, stats)

        ret, buffer = cv2.imencode('.jpeg', frame_vis)
        frame_vis = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-type: image/jpeg\r\n\r\n' + frame_vis + b'\r\n')

    camera.close()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', debug=True)
