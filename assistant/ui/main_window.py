
import sys
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Signal, Qt
from .events import EventBus
from .bridge import build_default
from .orb_widget import OrbWidget
from .states import IDLE, LISTENING, THINKING, SPEAKING, ERROR, WAKE

STATUS_TEXT = {
    IDLE: "Ready",
    WAKE: "Waking...",
    LISTENING: "Listening...",
    THINKING: "Thinking...",
    SPEAKING: "Speaking...",
    ERROR: "Something went wrong",
}

class SiriWindow(QWidget):
    quit_requested = Signal()
    def __init__(self, bus=None, bridge=None):
        super().__init__()
        self.bus = bus or EventBus()
        self.bridge = bridge or build_default(self.bus)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(360, 400)
        self.glass = QWidget(self)
        self.glass.setGeometry(10,10,340,380)
        self.glass.setStyleSheet("QWidget {background: rgba(26,26,34,0.68); border: 1px solid rgba(255,255,255,0.12); border-radius: 32px;}")
        layout = QVBoxLayout(self.glass)
        layout.setContentsMargins(20,20,20,20)
        self.orb_widget = OrbWidget()
        self.status = QLabel(STATUS_TEXT[IDLE])
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("QLabel {background: rgba(255,255,255,0.14); border-radius: 16px; padding: 7px 18px; color: white; font-size: 13px;}")
        self.caption = QLabel("")
        self.caption.setAlignment(Qt.AlignCenter)
        self.caption.setWordWrap(True)
        self.caption.setStyleSheet("color: white; font-size: 12px;")
        close_btn = QPushButton("X")
        close_btn.setFixedSize(28,28)
        close_btn.clicked.connect(self.close_and_quit)
        top = QHBoxLayout()
        top.addStretch()
        top.addWidget(close_btn)
        layout.addLayout(top)
        layout.addWidget(self.orb_widget, alignment=Qt.AlignCenter)
        layout.addWidget(self.status, alignment=Qt.AlignCenter)
        layout.addWidget(self.caption, alignment=Qt.AlignCenter)
        layout.addStretch()
        self.bus.caption_changed.connect(self.set_caption)
        self.bus.listening_started.connect(lambda: self.set_state(LISTENING))
        self.bus.processing_started.connect(lambda: self.set_state(THINKING))
        self.bus.speaking_started.connect(lambda: self.set_state(SPEAKING))
        self.bus.task_completed.connect(lambda: self.set_state(IDLE))
        self.bus.task_failed.connect(lambda m: self.set_state(ERROR))

    def set_state(self, state):
        self.status.setText(STATUS_TEXT.get(state, str(state)))
        try:
            self.orb_widget.set_state(state)
        except:
            pass

    def set_caption(self, text):
        self.caption.setText(text[:120])

    def close_and_quit(self):
        print("[Bridge] stop called")
        try:
            if hasattr(self.bridge, 'listener') and self.bridge.listener:
                self.bridge.listener.stop()
        except: pass
        try:
            self.bridge.stop()
        except: pass
        QApplication.instance().quit()
        self.close()

    def start_listening(self):
        print("[Window] Orb shown - starting listener")
        if hasattr(self.bridge, 'listener') and self.bridge.listener:
            self.bridge.listener.start()
        self.bridge.handle_text("hello")
        return

def main():
    app = QApplication.instance() or QApplication(sys.argv)
    bus = EventBus()
    win = SiriWindow(bus)
    win.show()
    win.start_listening()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
