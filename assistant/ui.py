"""AI Krish orb window. Start with: ~/.ai-krish/venv/bin/python -m assistant.ui"""
import math
import sys
import threading

from PySide6.QtCore import QObject, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QKeySequence, QPainter, QRadialGradient, QShortcut
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLineEdit, QPlainTextEdit,
    QPushButton, QVBoxLayout, QWidget, QLabel,
)

from assistant.commands import Router
from assistant.config import db_path
from assistant.desktop import Desktop
from assistant.listen import Listener, ListenResult, is_listen_command
from assistant.reminders import Reminders
from assistant.speech import Speaker
from assistant.storage import NoteStore
from assistant.ui_logic import run_command

COLORS = {
    "idle": QColor(80, 140, 255),
    "listening": QColor(255, 90, 90),
    "busy": QColor(255, 190, 60),
}


class Orb(QWidget):
    def __init__(self):
        super().__init__()
        self.state = "idle"
        self.phase = 0.0
        self.setMinimumSize(160, 160)
        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(40)

    def set_state(self, state):
        self.state = state
        self.update()

    def _tick(self):
        self.phase += 0.25 if self.state == "listening" else 0.08
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        base = min(w, h) * 0.30
        radius = base * (1 + 0.08 * math.sin(self.phase))
        color = COLORS[self.state]
        glow = QRadialGradient(w / 2, h / 2, radius * 1.8)
        faint = QColor(color)
        faint.setAlpha(0)
        strong = QColor(color)
        strong.setAlpha(120)
        glow.setColorAt(0.5, strong)
        glow.setColorAt(1.0, faint)
        p.setPen(Qt.NoPen)
        p.setBrush(glow)
        p.drawEllipse(QRectF(w / 2 - radius * 1.8, h / 2 - radius * 1.8, radius * 3.6, radius * 3.6))
        core = QRadialGradient(w / 2 - radius * 0.3, h / 2 - radius * 0.3, radius * 1.2)
        core.setColorAt(0, color.lighter(160))
        core.setColorAt(1, color.darker(150))
        p.setBrush(core)
        p.drawEllipse(QRectF(w / 2 - radius, h / 2 - radius, radius * 2, radius * 2))


class Bridge(QObject):
    """Lets background threads hand results to the window safely."""
    status = Signal(str)
    heard = Signal(object)
    reminder = Signal(str)


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Krish")
        self.resize(420, 560)
        self.bridge = Bridge()
        self.bridge.status.connect(lambda m: self.log("krish> " + m))
        self.bridge.heard.connect(self.on_heard)
        self.bridge.reminder.connect(self.on_reminder)

        self.speaker = Speaker()
        self.listener = Listener()
        self.router = Router(NoteStore(db_path()), Desktop())
        self.reminders = Reminders(self.bridge.reminder.emit)
        self.listening = False

        self.orb = Orb()
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.entry = QLineEdit()
        self.entry.setPlaceholderText("Type a command, e.g. open safari")
        self.entry.returnPressed.connect(self.on_enter)
        self.listen_button = QPushButton("Listen  (Option+Space)")
        self.listen_button.clicked.connect(self.start_listening)
        QShortcut(QKeySequence("Alt+Space"), self, activated=self.start_listening)

        row = QHBoxLayout()
        row.addWidget(self.entry)
        row.addWidget(self.listen_button)
        layout = QVBoxLayout(self)
        layout.addWidget(self.orb, 1)
        layout.addWidget(self.output, 2)
        layout.addLayout(row)
        self.log("krish> Ready. Type a command or press Listen. Type 'help' for examples.")

    def log(self, text):
        self.output.appendPlainText(text)

    def on_enter(self):
        line = self.entry.text().strip()
        self.entry.clear()
        if line:
            self.log("you> " + line)
            if is_listen_command(line):
                self.start_listening()
                return
            self.run(line)

    def run(self, line):
        self.orb.set_state("busy")
        text, should_quit = run_command(line, self.router, self.speaker, self.reminders)
        self.log("krish> " + text)
        self.orb.set_state("idle")
        if should_quit:
            self.close()

    def on_reminder(self, message):
        self.log("krish> " + message)
        self.speaker.speak(message)

    def start_listening(self):
        if self.listening:
            return
        self.listening = True
        self.listen_button.setEnabled(False)
        self.orb.set_state("listening")
        self.speaker.stop()
        self.router.pending = None  # a voice request can never answer a waiting yes/no

        def work():
            try:
                result = self.listener.listen_once(self.bridge.status.emit)
            except Exception as exc:
                result = ListenResult(None, "Listening failed: %s" % exc)
            self.bridge.heard.emit(result)

        threading.Thread(target=work, daemon=True).start()

    def on_heard(self, result):
        self.listening = False
        self.listen_button.setEnabled(True)
        self.orb.set_state("idle")
        if result.text is None:
            self.log("krish> " + result.error)
            return
        self.log("you (voice)> " + result.text)
        self.run(result.text)

    def closeEvent(self, event):
        self.reminders.stop()
        self.speaker.stop()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    window.raise_()
    window.activateWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
