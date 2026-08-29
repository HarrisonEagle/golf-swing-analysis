import numpy as np

ADDRESS_FRAME = 5
SMOOTHING_WINDOW = 5
TAKEAWAY_CONSECUTIVE_FRAMES = 2
DISPLACEMENT_RATIO = 0.06
MIN_DISPLACEMENT_PX = 8
VELOCITY_PERCENTILE = 70
VELOCITY_RATIO = 0.4
MIN_VELOCITY_PX = 1.5

PHASE_DESCRIPTIONS = {
    "address": "構え完了・静止状態",
    "takeaway_start": "クラブ・手元が実際に後方へ動き始めた瞬間",
    "top": "バックスイング最高到達点",
    "impact": "ボールインパクト",
    "finish": "スイング完了",
}


def detect_phases(frames):
    wrist_y = _wrist_height_series(frames)
    if wrist_y is None:
        return None

    smoothed_y = _moving_average(wrist_y, SMOOTHING_WINDOW)
    address = min(ADDRESS_FRAME, len(smoothed_y) - 1)
    takeaway_start = _detect_takeaway_start(frames, address)

    search_end = max(takeaway_start + 1, int(len(smoothed_y) * 0.75))
    top = takeaway_start + int(np.argmin(smoothed_y[takeaway_start:search_end]))

    impact_search_end = min(len(smoothed_y), top + 45)
    if top + 1 >= impact_search_end:
        impact = min(len(smoothed_y) - 1, top + 1)
    else:
        impact = top + int(np.argmax(smoothed_y[top:impact_search_end]))

    finish_search = smoothed_y[impact:]
    if len(finish_search) <= 1:
        finish = len(smoothed_y) - 1
    else:
        finish = impact + int(np.argmin(finish_search[1:])) + 1
        finish = min(finish, len(smoothed_y) - 1)

    return {
        "address": _phase_entry(frames, address, "address"),
        "takeaway_start": _phase_entry(frames, takeaway_start, "takeaway_start"),
        "top": _phase_entry(frames, top, "top"),
        "impact": _phase_entry(frames, impact, "impact"),
        "finish": _phase_entry(frames, finish, "finish"),
    }


def _detect_takeaway_start(frames, address_idx):
    wrist_x, wrist_y = _wrist_center_series(frames)
    if wrist_x is None:
        return min(address_idx + 1, len(frames) - 1)

    smooth_x = _moving_average(wrist_x, SMOOTHING_WINDOW)
    smooth_y = _moving_average(wrist_y, SMOOTHING_WINDOW)

    ref_x, ref_y = smooth_x[address_idx], smooth_y[address_idx]
    displacement = np.hypot(smooth_x - ref_x, smooth_y - ref_y)
    velocity = np.hypot(np.diff(smooth_x), np.diff(smooth_y))

    swing_range = np.max(displacement)
    disp_threshold = max(swing_range * DISPLACEMENT_RATIO, MIN_DISPLACEMENT_PX)
    vel_threshold = max(np.percentile(velocity, VELOCITY_PERCENTILE) * VELOCITY_RATIO, MIN_VELOCITY_PX)

    consecutive = 0
    for frame_idx in range(address_idx + 1, len(frames)):
        if (
            displacement[frame_idx] >= disp_threshold
            and velocity[frame_idx - 1] >= vel_threshold
        ):
            consecutive += 1
            if consecutive >= TAKEAWAY_CONSECUTIVE_FRAMES:
                return frame_idx - TAKEAWAY_CONSECUTIVE_FRAMES + 1
        else:
            consecutive = 0

    return min(address_idx + 1, len(frames) - 1)


def _phase_entry(frames, frame_idx, phase_name):
    return {
        "frame": frame_idx,
        "time_sec": frames[frame_idx]["time_sec"],
        "description": PHASE_DESCRIPTIONS[phase_name],
    }


def _wrist_center_series(frames):
    x_values, y_values = [], []
    for frame in frames:
        landmarks = frame["landmarks"]
        if not landmarks:
            x_values.append(np.nan)
            y_values.append(np.nan)
            continue
        x_values.append(
            (landmarks["LEFT_WRIST"]["x"] + landmarks["RIGHT_WRIST"]["x"]) / 2
        )
        y_values.append(
            (landmarks["LEFT_WRIST"]["y"] + landmarks["RIGHT_WRIST"]["y"]) / 2
        )

    if all(np.isnan(x_values)):
        return None, None

    x_series = np.array(x_values, dtype=float)
    y_series = np.array(y_values, dtype=float)
    x_series[np.isnan(x_series)] = np.nanmean(x_series)
    y_series[np.isnan(y_series)] = np.nanmean(y_series)
    return x_series, y_series


def _wrist_height_series(frames):
    _, wrist_y = _wrist_center_series(frames)
    return wrist_y


def _moving_average(values, window):
    if len(values) < window:
        return values
    kernel = np.ones(window) / window
    return np.convolve(values, kernel, mode="same")
