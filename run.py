import argparse
import logging

import cv2
from flask import Flask, Response, render_template

from trackstormsbot.camera import CameraStream
from trackstormsbot.controller import MotorController
from trackstormsbot.detectors import *
from trackstormsbot.utils import *

log = logging.getLogger(__name__)

app = Flask(__name__, template_folder='trackstormsbot/templates')

DETECTOR_MAP = {
    'haarcascade': CascadeDetector,
    'yunet': YuNetDetector,}


def get_args():
    parser = argparse.ArgumentParser('Trackstormsbot')
    parser.add_argument('-c', '--camera', type=int, default=0, help='Camera index')
    parser.add_argument('-d',
                        '--detector',
                        type=str,
                        default='yunet',
                        choices=DETECTOR_MAP.keys(),
                        help='Name of detector model to use')
    parser.add_argument('-p',
                        '--motor_ports',
                        type=str,
                        nargs=2,
                        default=['A', 'B'],
                        help='Motor Ports (X-axis, Y-axis)')
    parser.add_argument('--disable_controller', action='store_true', help='Disable controller')
    parser.add_argument('-r', '--detector_rate', type=int, default=-1, help='Detector rate (FPS)')
    return parser.parse_args()


def get_detector(detector_name, camera, rate, **kwargs):
    detector_class = DETECTOR_MAP[detector_name]
    return detector_class(camera, rate, **kwargs)


def video_stream():
    args = get_args()

    camera = CameraStream(args.camera)
    detector = get_detector(args.detector, camera, args.detector_rate)
    controller = MotorController(args.motor_ports)

    camera.open()
    detector.start()

    frame_size = camera.size()
    frame_middle = (frame_size[0] // 2, frame_size[1] // 2)

    while (camera.is_opened()):
        frame = camera.read()

        if frame is None:
            continue

        detections = detector.read()

        if len(detections) > 0:
            detection = detections[0]
        else:
            detection = None

        frame_vis = camera.read()

        if not args.disable_controller:
            if detection is not None:
                middle = calculate_middle_xywh(detection)
                frame_vis = visualise_detection(frame_vis, detection)
                controller.move_to_middle(
                    frame_middle=frame_middle,
                    detection_middle=middle,
                )
            else:
                controller.stop()

        stats = {
            'FPS (Camera)': int(camera.fps()),
            'FPS (Detector)': int(detector.fps()),}

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
