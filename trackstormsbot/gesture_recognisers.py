import mediapipe as mp
import numpy as np
import tflite_runtime.interpreter as tflite

from trackstormsbot.detectors import Detector


class KeyPointClassifier:

    def __init__(
        self,
        model_path='model/keypoint_classifier.tflite',
        num_threads=1,
    ):
        self.interpreter = tflite.Interpreter(model_path=model_path, num_threads=num_threads)

        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    def __call__(
        self,
        landmark_list,
    ):
        input_details_tensor_index = self.input_details[0]['index']
        landmark_list = [0, 0] + landmark_list  # add 2 zeros for base point
        self.interpreter.set_tensor(input_details_tensor_index, np.array([landmark_list], dtype=np.float32))
        self.interpreter.invoke()

        output_details_tensor_index = self.output_details[0]['index']

        result = self.interpreter.get_tensor(output_details_tensor_index)

        result_index = np.argmax(np.squeeze(result))

        return result_index


class MediapipeRecogniser(Detector):
    KEYPOINT_CLASSIFIER_PATH = 'trackstormsbot/models/keypoint_classifier.tflite'
    GESTURE_LABELS = ['open', 'close', 'point']

    def __init__(self, camera, rate=-1, det_frame_size=(128, 96), score_threshold=0.7):
        super().__init__(camera, rate, det_frame_size)
        self._score_threshold = score_threshold
        mp_hands = mp.solutions.hands
        self._model = mp_hands.Hands(
            max_num_hands=1,
            model_complexity=0,
            min_detection_confidence=self._score_threshold,
            min_tracking_confidence=self._score_threshold,
        )
        self._classifier = KeyPointClassifier(model_path=self.KEYPOINT_CLASSIFIER_PATH)

    def model_detection(self, frame):
        return self._model.process(frame)

    def detection_post_process(self, detections):
        landmarks = []
        for hand_landmarks in (detections.multi_hand_landmarks if detections.multi_hand_landmarks is not None else []):
            for landmark in hand_landmarks.landmark:
                landmarks.append((int(landmark.x * self._det_frame_size[0] * self._frame_scale_factor[0]),
                                  int(landmark.y * self._det_frame_size[1] * self._frame_scale_factor[1])))

        gesture = -1
        if len(landmarks) > 0:
            processed_landmarks = self._preprocess_landmarks(landmarks)
            gesture = self._classifier(processed_landmarks)

        return (landmarks, self._get_gesture_label(gesture))

    def _preprocess_landmarks(self, landmarks):
        processed_landmarks = []
        if len(landmarks) > 0:
            base_x, base_y = landmarks[0]
            for x, y in landmarks[1:]:
                processed_landmarks.append(x - base_x)
                processed_landmarks.append(y - base_y)

        # normalize list
        max_value = max(list(map(abs, processed_landmarks)))
        processed_landmarks = list(map(lambda x: x / max_value, processed_landmarks))

        return processed_landmarks

    def _get_gesture_label(self, gesture):
        return self.GESTURE_LABELS[gesture] if gesture >= 0 else 'None'
