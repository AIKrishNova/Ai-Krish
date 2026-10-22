from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from .events import BUS
from .orb_widget import OrbWidget
from .bridge import UIBridge
import threading

class SiriWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setFixedSize(360, 400)
        self.bridge = UIBridge()
        self.orb = OrbWidget()

        self.status = QLabel("Say Hey Krish")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 rgba(255,255,255,0.20), stop:1 rgba(255,255,255,0.10));
                border: 1px solid rgba(255,255,255,0.18);
                border-radius: 16px;
                padding: 7px 18px;
                color: white;
                font-size: 13px;
                font-weight: 600;
            }
        """)

        self.caption = QLabel("")
        self.caption.setAlignment(Qt.AlignCenter)
        self.caption.setWordWrap(True)
        self.caption.setStyleSheet("QLabel {background: transparent; color: rgba(255,255,255,0.9); font-size: 13px; padding: 4px;}")

        # Glass
        self.glass = QWidget(self)
        self.glass.setGeometry(10, 10, 340, 380)
        self.glass.setStyleSheet("QWidget {background: rgba(26,26,34,0.68); border: 1px solid rgba(255,255,255,0.12); border-radius: 32px;}")

        lay = QVBoxLayout()
        lay.setContentsMargins(24, 22, 24, 18)
        lay.addWidget(self.status, alignment=Qt.AlignCenter)
        lay.addStretch()
        lay.addWidget(self.orb, alignment=Qt.AlignCenter)
        lay.addStretch()
        lay.addWidget(self.caption)

        btn_style = """
            QPushButton {
                background: rgba(255,255,255,0.12);
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 18px;
                color: rgba(255,255,255,0.9);
                font-size: 13px;
                padding: 8px 14px;
                min-width: 44px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.20); }
        """
        self.btn_listen = QPushButton("◉")
        self.btn_stop = QPushButton("■")
        self.btn_cancel = QPushButton("✕")
        self.btn_listen.setToolTip("Listen")
        for b in (self.btn_listen, self.btn_stop, self.btn_cancel):
            b.setStyleSheet(btn_style)
            b.setFixedSize(42, 36)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(self.btn_listen)
        row.addWidget(self.btn_stop)
        row.addWidget(self.btn_cancel)
        row.addStretch()
        lay.addLayout(row)

        container = QWidget(self)
        container.setGeometry(10, 10, 340, 380)
        container.setAttribute(Qt.WA_TranslucentBackground, True)
        container.setStyleSheet("background: transparent;")
        container.setLayout(lay)

        BUS.wake_detected.connect(self.on_wake)
        BUS.listening_started.connect(lambda: self.set_state("listening","Listening…"))
        BUS.audio_level.connect(self.orb.set_audio)
        BUS.processing_started.connect(lambda: self.set_state("thinking","Thinking…"))
        BUS.speaking_started.connect(lambda t: self.set_state("speaking", t[:70]))
        BUS.task_completed.connect(lambda t: self.set_state("idle", t[:70]) or self.fade_out())
        BUS.task_failed.connect(lambda t: self.set_state("error", t[:90]))
        BUS.task_cancelled.connect(self.close)

        self.btn_listen.clicked.connect(self.start_listening)
        self.btn_stop.clicked.connect(self.stop_all)
        self.btn_cancel.clicked.connect(self.close)
        self.hide()

    def set_state(self, state, text=""):
        self.orb.set_state(state)
        m = {"idle":"Say Hey Krish","listening":"Listening…","thinking":"Thinking…","speaking":"Speaking…","error":"Oops"}
        self.status.setText(m.get(state, state))
        self.caption.setText(text if state!="idle" else "")
        # hide buttons in idle - pure Siri
        show_btns = state in ("listening","speaking","thinking")
        for b in (self.btn_stop, self.btn_cancel):
            b.setVisible(show_btns)
        self.btn_listen.setVisible(not show_btns)

    def on_wake(self):
        self.show()
        self.raise_()
        self.setWindowOpacity(0)
        a = QPropertyAnimation(self, b"windowOpacity", self)
        a.setDuration(360)
        a.setStartValue(0)
        a.setEndValue(1)
        a.setEasingCurve(QEasingCurve.OutCubic)
        a.start()
        self._a = a
        self.start_listening()

    def start_listening(self):
        self.show()
        BUS.listening_started.emit()
        def run():
            r = self.bridge.listener.listen_once(lambda _: None)
            if r.text:
                self.bridge.handle_text(r.text)
            else:
                BUS.task_failed.emit(r.error or "No speech")
        threading.Thread(target=run, daemon=True).start()

    def stop_all(self):
        self.bridge.speaker.stop()
        BUS.task_cancelled.emit()

    def fade_out(self):
        QTimer.singleShot(2600, self.close)
