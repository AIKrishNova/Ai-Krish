"""Animation formulas for the orb. Pure math, no Qt."""
import math


def clamp01(x):
    return max(0.0, min(1.0, float(x)))


def breathing_scale(t, period=4.0):
    """Idle breathing: 0.95 to 1.05 over one period."""
    return 1.0 + 0.05 * math.sin(2 * math.pi * t / period)


def listening_scale(level):
    """Orb size follows the microphone level (0 to 1)."""
    return 0.92 + 0.30 * clamp01(level)


def ring_progress(t, index, count=3, period=2.0):
    """0 to 1 progress of an expanding ring; rings are evenly staggered."""
    return ((t / period) - index / float(count)) % 1.0


def ring_look(progress):
    """(radius multiplier, alpha 0 to 1) for a ring at this progress."""
    return 1.0 + 0.9 * progress, 0.4 * (1.0 - progress)


def particle_positions(t, count=8, radius=1.0, period=3.0):
    points = []
    for i in range(count):
        angle = 2 * math.pi * (t / period + i / float(count))
        points.append((radius * math.cos(angle), radius * math.sin(angle)))
    return points


def bar_heights(t, count=5):
    """Waveform bar heights, each between 0.3 and 1.0."""
    return [0.3 + 0.7 * (0.5 + 0.5 * math.sin(t * 6.0 + i * 1.3)) for i in range(count)]


def shake_offset(since, duration=0.5, amplitude=8.0):
    """Horizontal shake in pixels after an error; zero once it has finished."""
    if since < 0 or since >= duration:
        return 0.0
    decay = 1.0 - since / duration
    return amplitude * decay * math.sin(since * 2 * math.pi * 8)


def hue_shift(t, period=6.0, degrees=40.0):
    """Gentle hue drift while thinking, in degrees."""
    return degrees * math.sin(2 * math.pi * t / period)
