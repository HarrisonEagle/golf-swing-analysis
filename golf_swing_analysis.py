import cv2
import json
import os

from utils.swing_analyzer import analyze_swing
from utils.video_utils import create_video_capture, create_video_writer, read_corrected_frame
from utils.visualizer import render_frame

INPUT_DIR = "input"
OUTPUT_DIR = "output"
JSON_DIR = os.path.join(OUTPUT_DIR, "swing_data")
VIDEO_DIR = os.path.join(OUTPUT_DIR, "videos")
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}


def process_video(input_path):
    swing_data = analyze_swing(input_path)

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    json_path = os.path.join(JSON_DIR, f"{base_name}.json")
    video_path = os.path.join(VIDEO_DIR, f"{base_name}_annotated.mp4")

    _save_json(swing_data, json_path)
    _render_video(input_path, video_path, swing_data)

    print(f"JSON saved at: {json_path}")
    print(f"Video saved at: {video_path}")
    return swing_data


def _save_json(swing_data, json_path):
    export_data = {key: value for key, value in swing_data.items() if key != "pose_frames"}
    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(export_data, file, indent=2, ensure_ascii=False)


def _render_video(input_path, output_path, swing_data):
    cap, fps, frame_size, rotation = create_video_capture(input_path)
    writer = create_video_writer(output_path, fps, frame_size)

    frame_idx = 0
    while True:
        ret, frame = read_corrected_frame(cap, rotation)
        if not ret:
            break
        writer.write(render_frame(frame, frame_idx, swing_data))
        frame_idx += 1

    cap.release()
    writer.release()


def main():
    os.makedirs(JSON_DIR, exist_ok=True)
    os.makedirs(VIDEO_DIR, exist_ok=True)

    input_files = sorted(
        f for f in os.listdir(INPUT_DIR)
        if os.path.splitext(f)[1].lower() in VIDEO_EXTENSIONS
    )

    if not input_files:
        print(f"No video files found in {INPUT_DIR}/")
        return

    for filename in input_files:
        print(f"Processing {filename}...")
        process_video(os.path.join(INPUT_DIR, filename))

    cv2.destroyAllWindows()
    print("All videos processed.")


if __name__ == "__main__":
    main()
