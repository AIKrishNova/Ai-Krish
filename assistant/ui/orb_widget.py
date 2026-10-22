"""The painted orb. Needs PySide6.  Preview: python -m assistant.ui.orb_widget"""
import math
import sys

from PySide6.QtCore import (
    Property, QElapsedTimer, QEasingCurve, QPointF, QPropertyAnimation,
    QRectF, Qt, QTimer,
)
from PySide6.QtGui import QColor, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QWidget

from assistant.ui import orb_math as om
from assistant.ui.states import ERROR, IDLE, LISTENING, SPEAKING, THINKING, WAKE

C1, C2, C3 = "#a8f3ff", "#7a8cff", "#b983ff"
ERROR_RED = QColor("#ff4d6a")


def shifted(hex_color, degrees):
    c = QColor(hex_color)
    h, s, v, a = c.getHsv()
    c.setHsv(int((h + degrees) % 360), s, v, a)
    return c


def blend(a, b, m):
    m = om.clamp01(m)
    return QColor(
        int(a.red() + (b.red() - a.red()) * m),
        int(a.green() + (b.green() - a.green()) * m),
        int(a.blue() + (b.blue() - a.blue()) * m),
    )


def with_alpha(color, alpha):
    c = QColor(color)
    c.setAlpha(max(0, min(255, int(alpha))))
    return c


class OrbWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(200, 200)
        self._state = IDLE
        self._state_t0 = 0.0
        self._level = 0.0
        self._target_level = 0.0
        self._error_mix = 0.0
        self._clock = QElapsedTimer()
        self._clock.start()
        self._fade = QPropertyAnimation(self, b"errorMix", self)
        self._fade.setDuration(300)
        self._fade.setEasingCurve(QEasingCurve.OutCubic)
        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.PreciseTimer)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)   # about 60 fps

    # ---- public --------------------------------------------------------
    def set_state(self, state):
        if state == self._state:
            return
        self._state = state
        self._state_t0 = self._now()
        self._fade.stop()
        self._fade.setStartValue(self._error_mix)
        self._fade.setEndValue(1.0 if state == ERROR else 0.0)
        self._fade.start()

    def set_level(self, level):
        self._target_level = om.clamp01(level)

    def set_audio(self, level):
        self.set_level(level)

    def set_quality(self, high):
        self._timer.setInterval(16 if high else 33)

    # ---- animated property ----------------------------------------------
    def _get_mix(self):
        return self._error_mix

    def _set_mix(self, value):
        self._error_mix = value
        self.update()

    errorMix = Property(float, _get_mix, _set_mix)

    # ---- internals ------------------------------------------------------
    def _now(self):
        return self._clock.elapsed() / 1000.0

    def _tick(self):
        if self._state != LISTENING:
            self._target_level = 0.0
        self._level += (self._target_level - self._level) * 0.35
        self.update()

    def paintEvent(self, _event):
        t = self._now()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        shake = om.shake_offset(t - self._state_t0) if self._state == ERROR else 0.0
        cx, cy = w / 2.0 + shake, h / 2.0
        base = min(w, h) * 0.22

        if self._state == LISTENING:
            scale = om.listening_scale(self._level)
        elif self._state == THINKING:
            scale = 1.0 + 0.03 * math.sin(t * 5)
        else:
            scale = om.breathing_scale(t)
        r = base * scale

        drift = om.hue_shift(t) if self._state == THINKING else 0.0
        c1, c2, c3 = (blend(shifted(c, drift), ERROR_RED, self._error_mix * 0.85)
                      for c in (C1, C2, C3))

        self._paint_bloom(p, cx, cy, r, c2)
        self._paint_shadow(p, cx, cy, r)
        if self._state == LISTENING:
            self._paint_rings(p, cx, cy, r, t)
        self._paint_orb(p, cx, cy, r, c1, c2, c3)
        if self._state == SPEAKING:
            self._paint_bars(p, cx, cy, r, t)
        if self._state == THINKING:
            self._paint_particles(p, cx, cy, r, t)
        self._paint_highlight(p, cx, cy, r)
        p.end()

    def _paint_bloom(self, p, cx, cy, r, color):
        g = QRadialGradient(cx, cy, r * 2.4)
        g.setColorAt(0.35, with_alpha(color, 120))
        g.setColorAt(1.0, with_alpha(color, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawEllipse(QPointF(cx, cy), r * 2.4, r * 2.4)

    def _paint_shadow(self, p, cx, cy, r):
        p.save()
        p.translate(cx, cy + r * 1.35)
        p.scale(1.0, 0.22)
        g = QRadialGradient(0, 0, r * 0.95)
        g.setColorAt(0.0, QColor(0, 0, 0, 80))
        g.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawEllipse(QPointF(0, 0), r * 0.95, r * 0.95)
        p.restore()

    def _paint_orb(self, p, cx, cy, r, c1, c2, c3):
        g = QRadialGradient(cx - r * 0.3, cy - r * 0.35, r * 1.5)
        g.setColorAt(0.0, c1)
        g.setColorAt(0.55, c2)
        g.setColorAt(1.0, c3)
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawEllipse(QPointF(cx, cy), r, r)

    def _paint_highlight(self, p, cx, cy, r):
        p.save()
        p.translate(cx - r * 0.36, cy - r * 0.42)
        p.rotate(-30)
        p.scale(1.0, 0.62)
        g = QRadialGradient(0, 0, r * 0.3)
        g.setColorAt(0.0, QColor(255, 255, 255, 230))
        g.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawEllipse(QPointF(0, 0), r * 0.3, r * 0.3)
        p.restore()

    def _paint_rings(self, p, cx, cy, r, t):
        p.setBrush(Qt.NoBrush)
        for i in range(3):
            mult, alpha = om.ring_look(om.ring_progress(t, i))
            p.setPen(QPen(QColor(120, 200, 255, int(255 * alpha)), 1))
            p.drawEllipse(QPointF(cx, cy), r * mult, r * mult)

    def _paint_particles(self, p, cx, cy, r, t):
        p.setPen(Qt.NoPen)
        points = om.particle_positions(t, count=8, radius=r * 1.55)
        for i, (x, y) in enumerate(points):
            p.setBrush(QColor(255, 255, 255, 90 + i * 20))
            p.drawEllipse(QPointF(cx + x, cy + y), 3.5, 3.5)

    def _paint_bars(self, p, cx, cy, r, t):
        heights = om.bar_heights(t, 5)
        bar_w = r * 0.12
        gap = r * 0.10
        total = 5 * bar_w + 4 * gap
        x = cx - total / 2.0
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 190))
        for hgt in heights:
            bar_h = r * 0.9 * hgt
            p.drawRoundedRect(QRectF(x, cy - bar_h / 2.0, bar_w, bar_h), bar_w / 2.0, bar_w / 2.0)
            x += bar_w + gap


def _preview():
    from PySide6.QtWidgets import QApplication, QVBoxLayout

    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("Orb preview")
    window.setStyleSheet("background-color: #12121a;")
    window.resize(360, 360)
    orb = OrbWidget()
    layout = QVBoxLayout(window)
    layout.addWidget(orb)
    states = [IDLE, WAKE, LISTENING, THINKING, SPEAKING, ERROR]
    index = {"i": -1}

    def next_state():
        index["i"] = (index["i"] + 1) % len(states)
        orb.set_state(states[index["i"]])
        print("state:", states[index["i"]])

    def fake_level():
        orb.set_level(0.5 + 0.45 * math.sin(orb._now() * 7))

    cycle = QTimer()
    cycle.timeout.connect(next_state)
    cycle.start(3000)
    level = QTimer()
    level.timeout.connect(fake_level)
    level.start(50)
    next_state()
    window.show()
    window.raise_()
    sys.exit(app.exec())


if __name__ == "__main__":
    _preview()
