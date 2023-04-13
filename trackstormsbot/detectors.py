import logging
import time
from threading import Thread

import cv2
import mediapipe as mp

log = logging.getLogger(__name__)


class Detector:

    def __init__(self, camera, rate=-1, det_frame_size=(320, 200)):
        self._camera = camera
        self._rate = rate
        self._det_frame_size = det_frame_size
        self._stopped = False
        self._detections = []
        self._labels = []
        self._fps = 1

        camera_frame_size = self._camera.size()
        self._frame_scale_factor = (
            camera_frame_size[0] / self._det_frame_size[0],
            camera_frame_size[1] / self._det_frame_size[1],
        )
        self._last_detection_time = 0
        self._thread = Thread(target=self.detect, args=())

    def start(self):
        self._stopped = False
        self._thread.start()

    def stop(self):
        self._stopped = True

    def read(self):
        return self._detections, self._labels

    def get_frame(self):
        frame = self._camera.read()

        # Resize frame to detection frame size
        if frame is not None:
            frame = cv2.resize(frame, self._det_frame_size, interpolation=cv2.INTER_AREA)

        return frame

    def fps(self):
        return self._fps

    def detect(self):
        frame_count = 0

        fps_timer = time.time()
        while not self._stopped:
            start_time = time.time()

            # Get frame
            frame = self.get_frame()
            if frame is None:
                continue

            # Run detection model and post process detections
            # These functions should be implemented by the child class
            output = self.model_detection(frame)
            self._detections, self._labels = self.detection_post_process(output)

            # Calculate detection rate
            frame_count += 1
            camera_fps = int(self._camera.fps())
            if camera_fps > 0 and frame_count % camera_fps == 0:
                self._fps = frame_count / (time.time() - fps_timer)
                frame_count = 0
                fps_timer = time.time()

            self._last_detection_time = time.time()

            # Sleep to maintain detection rate
            time.sleep(max(0, 1 / self._rate - (time.time() - start_time)))

    def model_detection(self, frame):
        return []

    def detection_post_process(self, detections):
        return detections, []


class CascadeDetector(Detector):
    HAARCASCADE = 'trackstormsbot/configs/haarcascade_frontalface_default.xml'

    def __init__(self,
                 camera,
                 rate=-1,
                 det_frame_size=(320, 200),
                 scale_factor=1.1,
                 min_neighbors=3,
                 min_size=(10, 10),
                 max_size=(100, 100)):
        super().__init__(camera, rate, det_frame_size)
        self._scale_factor = scale_factor
        self._min_neighbors = min_neighbors
        self._min_size = min_size
        self._max_size = max_size
        self._cascade = cv2.CascadeClassifier(self.HAARCASCADE)

    def model_detection(self, frame):
        return self._cascade.detectMultiScale(
            image=frame,
            scaleFactor=self._scale_factor,
            minNeighbors=self._min_neighbors,
            minSize=self._min_size,
            maxSize=self._max_size,
        )

    def detection_post_process(self, detections):
        processed_detections = [[
            int(x * self._frame_scale_factor[0]),
            int(y * self._frame_scale_factor[1]),
            int(w * self._frame_scale_factor[0]),
            int(h * self._frame_scale_factor[1]),] for (x, y, w, h) in detections]
        return processed_detections, []

    def get_frame(self):
        frame = self._camera.read()

        # Also convert to grayscale and equalize histogram
        if frame is not None:
            frame = cv2.resize(frame, self._det_frame_size, interpolation=cv2.INTER_AREA)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = cv2.equalizeHist(frame)

        return frame


class YuNetDetector(Detector):
    MODEL_PATH = 'trackstormsbot/models/face_detection_yunet_2022mar.onnx'

    def __init__(self, camera, rate=-1, det_frame_size=(128, 96), score_threshold=0.7, nms_threshold=0.3, top_k=10):
        super().__init__(camera, rate, det_frame_size)
        self._score_threshold = score_threshold
        self._nms_threshold = nms_threshold
        self._top_k = top_k
        self._model = cv2.FaceDetectorYN.create(
            self.MODEL_PATH,
            '',
            det_frame_size,
            score_threshold,
            nms_threshold,
            top_k,
        )

    def model_detection(self, frame):
        return self._model.detect(frame)

    def detection_post_process(self, detections):
        processed_detections = []
        for detection in (detections[1] if detections[1] is not None else []):
            try:
                x = int(detection[0] * self._frame_scale_factor[0])
                y = int(detection[1] * self._frame_scale_factor[1])
                w = int(detection[2] * self._frame_scale_factor[0])
                h = int(detection[3] * self._frame_scale_factor[1])
                processed_detections.append([x, y, w, h])
            except Exception as e:
                continue

        return processed_detections, []


class MediapipeDetector(Detector):

    def __init__(self, camera, rate=-1, det_frame_size=(128, 96), score_threshold=0.7):
        super().__init__(camera, rate, det_frame_size)
        self._score_threshold = score_threshold

        mp_face_detection = mp.solutions.face_detection
        self._model = mp_face_detection.FaceDetection(model='short', min_detection_confidence=self._score_threshold)

    def model_detection(self, frame):
        return self._model.process(frame)

    def detection_post_process(self, detections):
        processed_detections = []
        for detection in (detections.detections if detections.detections is not None else []):
            x = int(detection.location_data.relative_bounding_box.xmin * self._det_frame_size[0] *
                    self._frame_scale_factor[0])
            y = int(detection.location_data.relative_bounding_box.ymin * self._det_frame_size[1] *
                    self._frame_scale_factor[1])
            w = int(detection.location_data.relative_bounding_box.width * self._det_frame_size[0] *
                    self._frame_scale_factor[0])
            h = int(detection.location_data.relative_bounding_box.height * self._det_frame_size[1] *
                    self._frame_scale_factor[1])
            processed_detections.append([x, y, w, h])

        return processed_detections, []
