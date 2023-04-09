import logging

import cv2
from flask import Flask,Response, render_template

from camera import CameraStream
from controller import MotorController
from detectors import CascadeDetector
from utils import *

log = logging.getLogger(__name__)

app = Flask(__name__)

THREADS = 4
MODEL = 'efficientdet_lite0.tflite'
HAARCASCADE = "configs/haarcascade_frontalface_default.xml"

def video_stream():
    camera = CameraStream()
    detector = CascadeDetector(camera, HAARCASCADE)
    controller = MotorController('A', 'B')

    camera.open()
    detector.start()

    frame_size = camera.size()
    frame_middle = (frame_size[0]//2, frame_size[1]//2)

    while(camera.is_opened()):
            frame = camera.read()
            
            if frame is None:
                continue

            detections = detector.read()
            
            if len(detections) > 0:
                detection = detections[0]
            else:
                detection = None
            
            frame_vis = camera.read()

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
                "FPS (Camera)": int(camera.fps()),
                "FPS (Detector)": int(detector.fps()),
            }

            frame_vis = visualise_stats(frame_vis, stats)
            

            ret, buffer = cv2.imencode('.jpeg', frame_vis)
            frame_vis = buffer.tobytes()
            yield (b'--frame\r\n' b'Content-type: image/jpeg\r\n\r\n' + frame_vis + b'\r\n')

    camera.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(video_stream(), mimetype= 'multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(host ='0.0.0.0', debug=True)



