import numpy as np


def to_point(landmark):
    return np.array([landmark["x"], landmark["y"]], dtype=float)


def midpoint(a, b):
    return (to_point(a) + to_point(b)) / 2


def angle_between_points(a, b, c):
    """Return angle ABC in degrees."""
    a, b, c = to_point(a), to_point(b), to_point(c)
    ba = a - b
    bc = c - b
    denom = np.linalg.norm(ba) * np.linalg.norm(bc)
    if denom == 0:
        return 0.0
    cos_angle = np.dot(ba, bc) / denom
    return float(np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0))))


def line_angle_from_horizontal(a, b):
    """Return absolute angle of line AB from horizontal, in degrees."""
    a, b = to_point(a), to_point(b)
    delta = b - a
    return float(abs(np.degrees(np.arctan2(delta[1], delta[0]))))


def spine_angle_from_vertical(shoulder_mid, hip_mid):
    """Return spine tilt from vertical in degrees."""
    delta = shoulder_mid - hip_mid
    if np.linalg.norm(delta) == 0:
        return 0.0
    angle_from_vertical = np.degrees(np.arctan2(abs(delta[0]), abs(delta[1])))
    return float(angle_from_vertical)


def distance(a, b):
    return float(np.linalg.norm(to_point(a) - to_point(b)))
