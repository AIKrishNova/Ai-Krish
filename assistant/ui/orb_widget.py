from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QRadialGradient, QColor, QPen
import math, random

class OrbWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._scale = 1.0
        self._hue = 0
        self.state = "idle"
        self.audio = 0.0
        self.particles = [random.random()*6.28 for _ in range(8)]
        self.setFixedSize(220, 220)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16) # 60fps
        self.angle = 0

    def tick(self):
        self.angle += 0.02
        if self.state == "idle":
            self._scale = 1.0 + math.sin(self.angle*0.6)*0.04
        elif self.state == "listening":
            self._scale = 1.0 + self.audio*0.35 + math.sin(self.angle*3)*0.02
        elif self.state == "thinking":
            self._hue = (self._hue + 0.8) % 360
            for i in range(len(self.particles)):
                self.particles[i] += 0.05 + i*0.01
        elif self.state == "speaking":
            self._scale = 1.0 + abs(math.sin(self.angle*5))*0.18
        self.update()

    def set_state(self, s):
        self.state = s

    def set_audio(self, lvl):
        self.audio = max(0,min(1,lvl))

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx, cy = 110, 110
        r = 65 * self._scale

        # outer glow
        for i in range(3):
            glow = QColor(120, 180, 255, int(25 - i*8))
            p.setBrush(glow)
            p.setPen(Qt.NoPen)
            p.drawEllipse(int(cx-r-i*12), int(cy-r-i*12), int((r+i*12)*2), int((r+i*12)*2))

        # main orb gradient
        grad = QRadialGradient(cx-20, cy-25, r*1.6)
        grad.setColorAt(0, QColor("#e8fbff"))
        grad.setColorAt(0.2, QColor("#8af0ff"))
        grad.setColorAt(0.5, QColor("#7a8cff"))
        grad.setColorAt(0.8, QColor("#b983ff"))
        grad.setColorAt(1, QColor("#5a5cff"))
        p.setBrush(grad)
        p.setPen(Qt.NoPen)
        p.drawEllipse(int(cx-r), int(cy-r), int(r*2), int(r*2))

        # rings in listening
        if self.state == "listening":
            pen = QPen(QColor(120,200,255,90), 1.2)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            for k in range(3):
                rr = r + 20 + k*18 + math.sin(self.angle*2+k)*4
                p.drawEllipse(int(cx-rr), int(cy-rr), int(rr*2), int(rr*2))

        # particles in thinking
        if self.state == "thinking":
            p.setBrush(QColor(255,255,255,200))
            p.setPen(Qt.NoPen)
            for ph in self.particles:
                px = cx + math.cos(ph)* (r+28)
                py = cy + math.sin(ph)* (r+28)
                p.drawEllipse(int(px-3), int(py-3), 6, 6)

        # waveform in speaking
        if self.state == "speaking":
            pen = QPen(QColor(255,255,255,180), 2)
            p.setPen(pen)
            for i in range(5):
                h = 8 + abs(math.sin(self.angle*4+i))*18
                x = cx - 24 + i*12
                p.drawLine(int(x), int(cy-h/2), int(x), int(cy+h/2))
