import cv2
from threading import Thread
import time
import logging

log = logging.getLogger(__name__)

class CameraStream:
    def __init__(self, size=(640, 480), index=0):
        self._stopped = False
        self._status = False
        self._frame = None
        self._cap = cv2.VideoCapture(index)
        if size is not None:
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, size[0])
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, size[1])
        self._size = (int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        self._fps = -1
        self._thread = Thread(target=self.update, args=())

    def open(self):
        self._stopped = False
        log.info(f"Starting camera stream with size {self._size} and fps {self._cap.get(cv2.CAP_PROP_FPS)}")
        self._thread.start()

    def close(self):
        self._stopped = True

    def update(self):
        reported_fps = int(self._cap.get(cv2.CAP_PROP_FPS))
        frame_count = 0
        start_time = time.time()
        
        while not self._stopped:
            status, frame = self._cap.read()

            self._frame = frame
            self._status = status
            
            if not self._status:
                self.close()
                break

            frame_count += 1

            if frame_count % reported_fps == 0:
                self._fps = frame_count / (time.time() - start_time)
                frame_count = 0
                start_time = time.time()
            
        self._cap.release()
        self._cap = None
    
    def read(self):
        return None if not self._status else self._frame.copy()
    
    def is_opened(self):
        return not self._stopped
    
    def size(self):
        return self._size
    
    def fps(self):
        return self._fps
    
    
