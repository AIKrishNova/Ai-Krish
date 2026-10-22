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
        self.setFixedSize(360, 420)
        self.bridge = UIBridge()
        self.orb = OrbWidget()
        self.status = QLabel("Say Hey Krish")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("QLabel {background: rgba(255,255,255,0.14); border: 1px solid rgba(255,255,255,0.18); border-radius: 14px; padding: 6px 16px; color: rgba(255,255,255,0.92); font-size: 13px; font-weight: 600; font-family: -apple-system;}")
        self.caption = QLabel("")
        self.caption.setAlignment(Qt.AlignCenter)
        self.caption.setWordWrap(True)
        self.caption.setStyleSheet("QLabel {background: transparent; color: rgba(255,255,255,0.88); font-size: 13px; font-family: -apple-system; padding: 8px;}")
        self.glass = QWidget(self)
        self.glass.setGeometry(10, 10, 340, 400)
        self.glass.setStyleSheet("QWidget {background: rgba(28,28,36,0.72); border: 1px solid rgba(255,255,255,0.12); border-radius: 32px;}")
        self.glass.lower()
        lay = QVBoxLayout()
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)
        lay.addWidget(self.status, alignment=Qt.AlignCenter)
        lay.addStretch()
        lay.addWidget(self.orb, alignment=Qt.AlignCenter)
        lay.addStretch()
        lay.addWidget(self.caption)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(14)
        btn_style = "QPushButton {background: rgba(255,255,255,0.14); border: 1px solid rgba(255,255,255,0.12); border-radius: 20px; color: white; font-size: 12px; padding: 10px 14px; min-width: 52px;} QPushButton:hover {background: rgba(255,255,255,0.22);}"
        self.btn_listen = QPushButton("● Listen")
        self.btn_stop = QPushButton("Stop")
        self.btn_cancel = QPushButton("✕")
        for b in (self.btn_listen, self.btn_stop, self.btn_cancel):
            b.setStyleSheet(btn_style)
            b.setCursor(Qt.PointingHandCursor)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_listen)
        btn_row.addWidget(self.btn_stop)
        btn_row.addWidget(self.btn_cancel)
        btn_row.addStretch()
        lay.addLayout(btn_row)
        container = QWidget(self)
        container.setGeometry(10, 10, 340, 400)
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
        texts = {"idle":"Say Hey Krish","listening":"Listening…","thinking":"Thinking…","speaking":"Speaking…","error":"Oops"}
        self.status.setText(texts.get(state, state))
        self.caption.setText(text if state!="idle" else "")
    def on_wake(self):
        self.show()
        self.raise_()
        self.setWindowOpacity(0)
        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(380)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        self._anim = anim
        self.start_listening()
    def start_listening(self):
        self.show()
        BUS.listening_started.emit()
        def run():
            res = self.bridge.listener.listen_once(lambda m: None)
            if res.text:
                BUS.transcript_updated.emit(res.text, True)
                self.bridge.handle_text(res.text)
            else:
                BUS.task_failed.emit(res.error or "No speech")
        threading.Thread(target=run, daemon=True).start()
    def stop_all(self):
        self.bridge.speaker.stop()
        BUS.task_cancelled.emit()
    def fade_out(self):
        QTimer.singleShot(2600, self.close)
