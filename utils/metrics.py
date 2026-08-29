from utils.geometry import (
    angle_between_points,
    distance,
    line_angle_from_horizontal,
    midpoint,
    spine_angle_from_vertical,
)


def compute_phase_metrics(landmarks, address_landmarks=None):
    if not landmarks:
        return None

    shoulder_mid = midpoint(landmarks["LEFT_SHOULDER"], landmarks["RIGHT_SHOULDER"])
    hip_mid = midpoint(landmarks["LEFT_HIP"], landmarks["RIGHT_HIP"])

    metrics = {
        "spine_angle_deg": round(spine_angle_from_vertical(shoulder_mid, hip_mid), 1),
        "shoulder_line_angle_deg": round(
            line_angle_from_horizontal(landmarks["LEFT_SHOULDER"], landmarks["RIGHT_SHOULDER"]), 1
        ),
        "hip_line_angle_deg": round(
            line_angle_from_horizontal(landmarks["LEFT_HIP"], landmarks["RIGHT_HIP"]), 1
        ),
        "x_factor_deg": round(
            line_angle_from_horizontal(landmarks["LEFT_SHOULDER"], landmarks["RIGHT_SHOULDER"])
            - line_angle_from_horizontal(landmarks["LEFT_HIP"], landmarks["RIGHT_HIP"]),
            1,
        ),
        "lead_arm_angle_deg": round(
            angle_between_points(
                landmarks["LEFT_SHOULDER"],
                landmarks["LEFT_ELBOW"],
                landmarks["LEFT_WRIST"],
            ),
            1,
        ),
        "trail_arm_angle_deg": round(
            angle_between_points(
                landmarks["RIGHT_SHOULDER"],
                landmarks["RIGHT_ELBOW"],
                landmarks["RIGHT_WRIST"],
            ),
            1,
        ),
        "lead_knee_angle_deg": round(
            angle_between_points(
                landmarks["LEFT_HIP"],
                landmarks["LEFT_KNEE"],
                landmarks["LEFT_ANKLE"],
            ),
            1,
        ),
        "trail_knee_angle_deg": round(
            angle_between_points(
                landmarks["RIGHT_HIP"],
                landmarks["RIGHT_KNEE"],
                landmarks["RIGHT_ANKLE"],
            ),
            1,
        ),
        "left_wrist": _point_dict(landmarks["LEFT_WRIST"]),
        "right_wrist": _point_dict(landmarks["RIGHT_WRIST"]),
        "shoulder_mid": _point_dict_from_array(shoulder_mid),
        "hip_mid": _point_dict_from_array(hip_mid),
    }

    if address_landmarks:
        head_ref = address_landmarks.get("NOSE") or address_landmarks["RIGHT_EAR"]
        metrics["head_movement_px"] = round(distance(landmarks["NOSE"], head_ref), 1)

    return metrics


def compute_tempo(phases):
    address_time = phases["address"]["time_sec"]
    takeaway_time = phases["takeaway_start"]["time_sec"]
    top_time = phases["top"]["time_sec"]
    impact_time = phases["impact"]["time_sec"]
    finish_time = phases["finish"]["time_sec"]

    address_hold = max(takeaway_time - address_time, 0)
    backswing = max(top_time - takeaway_time, 0)
    downswing = max(impact_time - top_time, 0)
    follow_through = max(finish_time - impact_time, 0)
    real_tempo_ratio = round(backswing / downswing, 2) if downswing > 0 else None

    return {
        "address_hold_sec": round(address_hold, 3),
        "backswing_sec": round(backswing, 3),
        "downswing_sec": round(downswing, 3),
        "follow_through_sec": round(follow_through, 3),
        "real_tempo_ratio": real_tempo_ratio,
    }


def _point_dict(landmark):
    return {"x": landmark["x"], "y": landmark["y"]}


def _point_dict_from_array(point):
    return {"x": round(float(point[0]), 1), "y": round(float(point[1]), 1)}
