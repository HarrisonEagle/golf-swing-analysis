import cv2
import numpy as np

from utils.geometry import midpoint

COLORS = {
    "spine": (0, 200, 255),
    "torso": (0, 20, 200),
    "arm": (255, 180, 0),
    "joint": (0, 255, 255),
    "wrist": (0, 0, 255),
    "axis": (200, 200, 200),
    "text": (0, 255, 0),
    "phase": (255, 255, 255),
}

PHASE_LABELS = {
    "address": "Address",
    "takeaway_start": "Takeaway",
    "top": "Top",
    "impact": "Impact",
    "finish": "Finish",
}

# Landscape 720x480 を基準に、短辺に比例してテキストサイズを調整する。
REFERENCE_SHORT_SIDE = 480
PHASE_FONT_SCALE = 0.82
METRICS_FONT_SCALE = 0.46


def _overlay_layout(frame_w, frame_h):
    scale = min(frame_w, frame_h) / REFERENCE_SHORT_SIDE
    margin = max(int(round(16 * scale)), 8)

    return {
        "margin": margin,
        "phase_scale": PHASE_FONT_SCALE * scale,
        "metrics_scale": METRICS_FONT_SCALE * scale,
        "phase_thickness": max(int(round(2 * scale)), 1),
        "metrics_thickness": max(int(round(2 * scale)), 1),
        "phase_y": margin + int(round(26 * scale)),
        "metrics_start_y": margin + int(round(54 * scale)),
        "line_spacing": max(int(round(22 * scale)), 14),
    }


def render_frame(frame, frame_idx, swing_data):
    frame_h, frame_w = frame.shape[:2]
    annotated = frame.copy()
    layout = _overlay_layout(frame_w, frame_h)
    phases = swing_data["phases"]
    current_phase = _phase_for_frame(frame_idx, phases)

    pose_frame = swing_data["pose_frames"][frame_idx]
    landmarks = pose_frame["landmarks"]
    if landmarks:
        _draw_pose(annotated, landmarks, layout)
        if current_phase:
            _draw_phase_metrics(
                annotated,
                current_phase,
                swing_data["metrics"].get(current_phase),
                layout,
            )

    _draw_axes(annotated, frame_w, frame_h, layout)
    if current_phase:
        cv2.putText(
            annotated,
            PHASE_LABELS[current_phase],
            (layout["margin"], layout["phase_y"]),
            cv2.FONT_HERSHEY_SIMPLEX,
            layout["phase_scale"],
            COLORS["phase"],
            layout["phase_thickness"],
            cv2.LINE_AA,
        )

    return annotated


def _phase_for_frame(frame_idx, phases):
    ordered = ["address", "takeaway_start", "top", "impact", "finish"]
    current = ordered[0]
    for phase_name in ordered:
        if frame_idx >= phases[phase_name]["frame"]:
            current = phase_name
    return current


def _draw_pose(frame, landmarks, layout):
    scale = layout["phase_scale"] / PHASE_FONT_SCALE
    line_thickness = max(int(round(2 * scale)), 1)
    wrist_radius = max(int(round(7 * scale)), 4)
    joint_radius = max(int(round(4 * scale)), 2)
    spine_thickness = max(int(round(3 * scale)), 2)

    shoulder_mid = midpoint(landmarks["LEFT_SHOULDER"], landmarks["RIGHT_SHOULDER"])
    hip_mid = midpoint(landmarks["LEFT_HIP"], landmarks["RIGHT_HIP"])

    _draw_line(frame, landmarks["LEFT_SHOULDER"], landmarks["RIGHT_SHOULDER"], COLORS["torso"], line_thickness)
    _draw_line(frame, landmarks["LEFT_HIP"], landmarks["RIGHT_HIP"], COLORS["torso"], line_thickness)
    _draw_line_array(frame, shoulder_mid, hip_mid, COLORS["spine"], spine_thickness)

    for side in ("LEFT", "RIGHT"):
        _draw_line(frame, landmarks[f"{side}_SHOULDER"], landmarks[f"{side}_ELBOW"], COLORS["arm"], line_thickness)
        _draw_line(frame, landmarks[f"{side}_ELBOW"], landmarks[f"{side}_WRIST"], COLORS["arm"], line_thickness)
        _draw_line(frame, landmarks[f"{side}_SHOULDER"], landmarks[f"{side}_HIP"], COLORS["torso"], line_thickness)

    for name, landmark in landmarks.items():
        point = (int(landmark["x"]), int(landmark["y"]))
        if "WRIST" in name:
            cv2.circle(frame, point, wrist_radius, COLORS["wrist"], line_thickness)
            cv2.circle(frame, point, max(joint_radius - 1, 2), COLORS["wrist"], -1)
        elif name in {"LEFT_SHOULDER", "RIGHT_SHOULDER", "LEFT_ELBOW", "RIGHT_ELBOW", "LEFT_HIP", "RIGHT_HIP"}:
            cv2.circle(frame, point, joint_radius, COLORS["joint"], -1)


def _draw_phase_metrics(frame, phase_name, metrics, layout):
    if not metrics:
        return

    lines = [
        f"Spine: {metrics['spine_angle_deg']} deg",
        f"X-factor: {metrics['x_factor_deg']} deg",
        f"Lead arm: {metrics['lead_arm_angle_deg']} deg",
        f"Trail arm: {metrics['trail_arm_angle_deg']} deg",
    ]
    if phase_name != "address" and "head_movement_px" in metrics:
        lines.append(f"Head move: {metrics['head_movement_px']} px")

    y = layout["metrics_start_y"]
    for line in lines:
        cv2.putText(
            frame,
            line,
            (layout["margin"], y),
            cv2.FONT_HERSHEY_SIMPLEX,
            layout["metrics_scale"],
            COLORS["text"],
            layout["metrics_thickness"],
            cv2.LINE_AA,
        )
        y += layout["line_spacing"]


def _draw_line(frame, a, b, color, thickness):
    p1 = (int(a["x"]), int(a["y"]))
    p2 = (int(b["x"]), int(b["y"]))
    cv2.line(frame, p1, p2, color, thickness, cv2.LINE_AA)


def _draw_line_array(frame, a, b, color, thickness):
    p1 = (int(a[0]), int(a[1]))
    p2 = (int(b[0]), int(b[1]))
    cv2.line(frame, p1, p2, color, thickness, cv2.LINE_AA)


def _draw_axes(frame, frame_w, frame_h, layout):
    scale = layout["phase_scale"] / PHASE_FONT_SCALE
    margin = layout["margin"]
    origin = (margin, frame_h - margin)
    length = max(int(round(50 * scale)), 24)
    thickness = max(int(round(2 * scale)), 1)
    label_scale = max(0.35 * scale, 0.3)

    x_end = (origin[0] + length, origin[1])
    y_end = (origin[0], origin[1] - length)
    cv2.line(frame, origin, x_end, COLORS["axis"], thickness)
    cv2.line(frame, origin, y_end, COLORS["axis"], thickness)
    cv2.putText(frame, "X", (x_end[0] + 8, x_end[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, label_scale, COLORS["axis"], 1)
    cv2.putText(frame, "Y", (y_end[0] - 15, y_end[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, label_scale, COLORS["axis"], 1)
