import os

from utils.metrics import compute_phase_metrics, compute_tempo
from utils.phase_detector import detect_phases
from utils.pose_extractor import extract_poses


def analyze_swing(video_path):
    pose_data = extract_poses(video_path)
    frames = pose_data["frames"]
    phases = detect_phases(frames)

    if not phases:
        raise ValueError(f"Could not detect swing phases for {video_path}")

    address_landmarks = frames[phases["address"]["frame"]]["landmarks"]
    metrics = {}
    for phase_name, phase in phases.items():
        frame_landmarks = frames[phase["frame"]]["landmarks"]
        metrics[phase_name] = compute_phase_metrics(
            frame_landmarks,
            address_landmarks=address_landmarks if phase_name != "address" else None,
        )

    return {
        "video": os.path.basename(video_path),
        "fps": pose_data["fps"],
        "frame_count": pose_data["frame_count"],
        "frame_size": pose_data["frame_size"],
        "phases": phases,
        "metrics": metrics,
        "tempo": compute_tempo(phases),
        "pose_frames": frames,
    }
