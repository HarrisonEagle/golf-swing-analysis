import subprocess

import cv2


def probe_video_rotation(file_path):
    """Return rotation in degrees (counter-clockwise) needed for correct display."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream_side_data=rotation",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                file_path,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        value = result.stdout.strip()
        if value:
            return int(value) % 360
    except (subprocess.SubprocessError, ValueError, FileNotFoundError):
        pass
    return 0


def display_frame_size(raw_frame_size, rotation):
    frame_w, frame_h = raw_frame_size
    if rotation % 180 == 90:
        return (frame_h, frame_w)
    return (frame_w, frame_h)


def correct_frame_orientation(frame, rotation):
    if rotation == 0:
        return frame
    if rotation == 90:
        return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    if rotation == 180:
        return cv2.rotate(frame, cv2.ROTATE_180)
    if rotation == 270:
        return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    return frame


def create_video_capture(file_path):
    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        raise IOError(f"Unable to open video: {file_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    raw_frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    raw_frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    rotation = probe_video_rotation(file_path)
    frame_size = display_frame_size((raw_frame_w, raw_frame_h), rotation)

    return cap, fps, frame_size, rotation


def read_corrected_frame(cap, rotation):
    ret, frame = cap.read()
    if not ret:
        return False, None
    return True, correct_frame_orientation(frame, rotation)


def create_video_writer(output_path, fps, frame_size):
    return cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, frame_size)
