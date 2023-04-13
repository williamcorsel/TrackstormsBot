import cv2


def calculate_middle_xywh(detection):
    x, y, w, h = detection
    return x + w // 2, y + h // 2


def visualise_detection(frame, detection, color=(0, 255, 0), thickness=2):
    x, y, w, h = detection
    frame_out = cv2.rectangle(frame, (x, y), (x + w, y + h), color, thickness)
    return frame_out


def visualise_landmarks(frame, landmarks, color=(0, 255, 0), thickness=2):
    for landmark in landmarks:
        x, y = landmark
        frame = cv2.circle(frame, (x, y), 2, color, thickness)

    return frame


def visualise_stats(frame, stats, location=(10, 30), color=(0, 255, 0), thickness=2):
    for stat_name, stat_value in stats.items():
        stat = f'{stat_name}: {stat_value}'
        frame = cv2.putText(frame, stat, location, cv2.FONT_HERSHEY_SIMPLEX, 1, color, thickness)
        location = (location[0], location[1] + 30)

    return frame
