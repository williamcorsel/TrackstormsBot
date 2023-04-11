import time
from threading import Thread

import cv2


class Detector:

    def __init__(self, camera, det_frame_size=(320, 200)):
        self._camera = camera
        self._det_frame_size = det_frame_size
        self._stopped = False
        self._detections = []
        self._fps = -1

        camera_frame_size = self._camera.size()
        self._frame_scale_factor = (
            camera_frame_size[0] / self._det_frame_size[0],
            camera_frame_size[1] / self._det_frame_size[1],
        )
        self._thread = Thread(target=self.detect, args=())

    def start(self):
        self._stopped = False
        self._thread.start()

    def stop(self):
        self._stopped = True

    def read(self):
        return self._detections

    def get_frame(self):
        frame = self._camera.read()

        # Resize frame to detection frame size
        if frame is not None:
            frame = cv2.resize(frame, self._det_frame_size, interpolation=cv2.INTER_AREA)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = cv2.equalizeHist(frame)

        return frame

    def fps(self):
        return self._fps

    def detect(self):
        reported_fps = int(self._camera.fps())
        frame_count = 0
        start_time = time.time()

        while not self._stopped:
            self._detections = self.detect()

            frame_count += 1
            if frame_count % reported_fps == 0:
                self._fps = frame_count / (time.time() - start_time)
                frame_count = 0
                start_time = time.time()


class CascadeDetector(Detector):
    HAARCASCADE = 'trackstormsbot/configs/haarcascade_frontalface_default.xml'

    def __init__(self, camera, scale_factor=1.1, min_neighbors=3, min_size=(10, 10), max_size=(100, 100)):
        super().__init__(camera)
        self._scale_factor = scale_factor
        self._min_neighbors = min_neighbors
        self._min_size = min_size
        self._max_size = max_size
        self._cascade = cv2.CascadeClassifier(self.HAARCASCADE)

    def detect(self):
        reported_fps = int(self._camera.fps())
        frame_count = 0
        start_time = time.time()

        while not self._stopped:
            frame = self.get_frame()

            if frame is None:
                continue

            detections = self._cascade.detectMultiScale(
                image=frame,
                scaleFactor=self._scale_factor,
                minNeighbors=self._min_neighbors,
                minSize=self._min_size,
                maxSize=self._max_size,
            )

            # Scale detections to original frame size
            self._detections = [[
                int(x * self._frame_scale_factor[0]),
                int(y * self._frame_scale_factor[1]),
                int(w * self._frame_scale_factor[0]),
                int(h * self._frame_scale_factor[1]),] for (x, y, w, h) in detections]

            frame_count += 1
            if frame_count % reported_fps == 0:
                self._fps = frame_count / (time.time() - start_time)
                frame_count = 0
                start_time = time.time()
