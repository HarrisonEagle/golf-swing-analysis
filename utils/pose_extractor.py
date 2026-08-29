import cv2
import mediapipe as mp

from utils.video_utils import create_video_capture, read_corrected_frame

mp_pose = mp.solutions.pose

TRACKED_LANDMARKS = [
    "NOSE",
    "LEFT_EAR",
    "RIGHT_EAR",
    "LEFT_SHOULDER",
    "RIGHT_SHOULDER",
    "LEFT_ELBOW",
    "RIGHT_ELBOW",
    "LEFT_WRIST",
    "RIGHT_WRIST",
    "LEFT_HIP",
    "RIGHT_HIP",
    "LEFT_KNEE",
    "RIGHT_KNEE",
    "LEFT_ANKLE",
    "RIGHT_ANKLE",
]


def extract_poses(video_path):
    cap, fps, frame_size, rotation = create_video_capture(video_path)
    frame_w, frame_h = frame_size
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    frames = []
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        frame_idx = 0
        while True:
            ret, frame = read_corrected_frame(cap, rotation)
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)
            landmarks = _serialize_landmarks(results.pose_landmarks, frame_w, frame_h)

            frames.append({
                "frame": frame_idx,
                "time_sec": round(frame_idx / fps, 4),
                "landmarks": landmarks,
            })
            frame_idx += 1

    cap.release()

    return {
        "fps": fps,
        "frame_count": frame_count or len(frames),
        "frame_size": [frame_w, frame_h],
        "rotation": rotation,
        "frames": frames,
    }


def _serialize_landmarks(pose_landmarks, frame_w, frame_h):
    if not pose_landmarks:
        return None

    landmarks = {}
    for name in TRACKED_LANDMARKS:
        landmark_id = getattr(mp_pose.PoseLandmark, name)
        lm = pose_landmarks.landmark[landmark_id]
        landmarks[name] = {
            "x": round(lm.x * frame_w, 2),
            "y": round(lm.y * frame_h, 2),
            "z": round(lm.z, 4),
            "visibility": round(lm.visibility, 4),
        }
    return landmarks
