"""Small deterministic recipes. Not a renderer or replacement for an animation library."""
import math


def progress(t, start, duration):
    if not all(math.isfinite(x) for x in (t, start, duration)) or duration < 0:
        raise ValueError('Time values must be finite; duration must be nonnegative')
    if duration == 0:
        return float(t >= start)
    return max(0.0, min(1.0, (t - start) / duration))


def ease_out_cubic(p):
    p = max(0.0, min(1.0, p))
    return 1 - (1 - p) ** 3


def cover_transform(crop, window):
    cx, cy, cw, ch = crop
    width, height = window
    if not all(math.isfinite(v) for v in (*crop, *window)) or min(cw, ch, width, height) <= 0:
        raise ValueError('Crop and window dimensions must be positive and finite')
    scale = max(width / cw, height / ch)
    return scale, (width - scale * cw) / 2 - scale * cx, (height - scale * ch) / 2 - scale * cy


def project_point(point, transform):
    scale, left, top = transform
    return left + point[0] * scale, top + point[1] * scale


def frame_boundaries(durations, fps):
    """Round cumulative boundaries once (half up), avoiding per-shot drift."""
    if not math.isfinite(fps) or fps <= 0:
        raise ValueError('fps must be positive and finite')
    total, boundaries = 0.0, [0]
    for duration in durations:
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError('durations must be positive and finite')
        total += duration
        boundaries.append(math.floor(total * fps + 0.5))
    return boundaries
