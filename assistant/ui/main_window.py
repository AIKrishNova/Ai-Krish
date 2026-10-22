from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from .events import BUS
from .orb_widget import OrbWidget
from .bridge import UIBridge
import threading, numpy as np, sounddevice as sd

class SiriWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(380, 420)
        self.bridge = UIBridge()
        self.orb = OrbWidget()

        self.status = QLabel("Say Hey Krish")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("color:white; font-size:14px; font-weight:600;")

        self.caption = QLabel("")
        self.caption.setAlignment(Qt.AlignCenter)
        self.caption.setWordWrap(True)
        self.caption.setStyleSheet("color:rgba(255,255,255,0.85); font-size:13px;")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20,20,20,20)
        lay.addWidget(self.status)
        lay.addStretch()
        lay.addWidget(self.orb, alignment=Qt.AlignCenter)
        lay.addStretch()
        lay.addWidget(self.caption)

        btns = QHBoxLayout()
        self.btn_listen = QPushButton("Listen")
        self.btn_stop = QPushButton("Stop")
        self.btn_cancel = QPushButton("X")
        for b in (self.btn_listen, self.btn_stop, self.btn_cancel):
            b.setStyleSheet("background:rgba(255,255,255,0.12); color:white; border-radius:12px; padding:6px 10px;")
        btns.addWidget(self.btn_listen)
        btns.addWidget(self.btn_stop)
        btns.addWidget(self.btn_cancel)
        lay.addLayout(btns)

        self.setStyleSheet("background:rgba(22,22,30,0.78); border-radius:28px;")

        BUS.wake_detected.connect(self.on_wake)
        BUS.listening_started.connect(lambda: self.set_state("listening","Listening..."))
        BUS.audio_level.connect(self.orb.set_audio)
        BUS.processing_started.connect(lambda: self.set_state("thinking","Thinking..."))
        BUS.speaking_started.connect(lambda t: self.set_state("speaking", t[:80]))
        BUS.task_completed.connect(lambda t: self.fade_out())
        BUS.task_failed.connect(lambda t: self.set_state("error", t[:100]))
        BUS.task_cancelled.connect(self.close)

        self.btn_listen.clicked.connect(self.start_listening)
        self.btn_stop.clicked.connect(self.stop_all)
        self.btn_cancel.clicked.connect(self.close)
        self.hide()

    def set_state(self, state, text=""):
        self.orb.set_state(state)
        self.status.setText({"idle":"Say Hey Krish","listening":"Listening...","thinking":"Thinking...","speaking":"Speaking...","error":"Error"}.get(state,state))
        self.caption.setText(text)
        if state=="error":
            self.setStyleSheet("background:rgba(60,20,30,0.82); border-radius:28px;")
        else:
            self.setStyleSheet("background:rgba(22,22,30,0.78); border-radius:28px;")

    def on_wake(self):
        self.show()
        self.raise_()
        self.setWindowOpacity(0)
        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(350)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        self.anim = anim
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
                BUS.task_failed.emit(res.error)
        threading.Thread(target=run, daemon=True).start()

    def stop_all(self):
        self.bridge.speaker.stop()
        BUS.task_cancelled.emit()

    def fade_out(self):
        def hide_later():
            self.close()
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2500, hide_later)
