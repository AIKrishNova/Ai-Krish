"""Floating glass window. Every state comes from the event bus; nothing is faked here."""
import threading

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer, Signal
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from assistant.ui.orb_widget import OrbWidget
from assistant.ui.states import ERROR, IDLE, LISTENING, SPEAKING, THINKING, WAKE

STATUS_TEXT = {
    IDLE: "Ready",
    WAKE: "Waking\u2026",
    LISTENING: "Listening\u2026",
    THINKING: "Thinking\u2026",
    SPEAKING: "Speaking\u2026",
    ERROR: "Something went wrong",
}
HIDE_AFTER_MS = {IDLE: 2600, ERROR: 5000}

BUTTON_STYLE = """
QPushButton {
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 18px;
    color: rgba(255,255,255,0.9);
    font-size: 13px;
}
QPushButton:hover { background: rgba(255,255,255,0.20); }
"""


class SiriWindow(QWidget):
    quit_requested = Signal()

    def __init__(self, bus, bridge):
        super().__init__()
        self.bus = bus
        self.bridge = bridge
        self._busy = False
        self._anim = None
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setFixedSize(360, 400)

        self.glass = QWidget(self)
        self.glass.setGeometry(10, 10, 340, 380)
        self.glass.setStyleSheet(
            "QWidget {background: rgba(26,26,34,0.68);"
            " border: 1px solid rgba(255,255,255,0.12); border-radius: 32px;}"
        )

        self.orb = OrbWidget()
        self.status = QLabel(STATUS_TEXT[IDLE])
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet(
            "QLabel {background: rgba(255,255,255,0.14); border: 1px solid rgba(255,255,255,0.18);"
            " border-radius: 16px; padding: 7px 18px; color: white; font-size: 13px; font-weight: 600;}"
        )
        self.caption = QLabel("")
        self.caption.setAlignment(Qt.AlignCenter)
        self.caption.setWordWrap(True)
        self.caption.setStyleSheet(
            "QLabel {background: transparent; color: rgba(255,255,255,0.9); font-size: 13px; padding: 4px;}"
        )

        self.btn_listen = QPushButton("\u25c9")
        self.btn_listen.setToolTip("Listen")
        self.btn_stop = QPushButton("\u25a0")
        self.btn_stop.setToolTip("Stop speaking")
        self.btn_close = QPushButton("\u2715")
        self.btn_close.setToolTip("Hide")
        for b in (self.btn_listen, self.btn_stop, self.btn_close):
            b.setStyleSheet(BUTTON_STYLE)
            b.setFixedSize(42, 36)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(self.btn_listen)
        row.addWidget(self.btn_stop)
        row.addWidget(self.btn_close)
        row.addStretch()

        lay = QVBoxLayout()
        lay.setContentsMargins(24, 22, 24, 18)
        lay.addWidget(self.status, alignment=Qt.AlignCenter)
        lay.addStretch()
        lay.addWidget(self.orb, alignment=Qt.AlignCenter)
        lay.addStretch()
        lay.addWidget(self.caption)
        lay.addLayout(row)
        container = QWidget(self)
        container.setGeometry(10, 10, 340, 380)
        container.setAttribute(Qt.WA_TranslucentBackground, True)
        container.setStyleSheet("background: transparent;")
        container.setLayout(lay)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.fade_out)

        # Bound methods of QObjects: Qt delivers them on the GUI thread even
        # when the bridge emits from the worker thread.
        bus.state_changed.connect(self.on_state)
        bus.caption_changed.connect(self.on_caption)
        bus.task_failed.connect(self.on_failed)
        bus.audio_level.connect(self.orb.set_level)

        self.btn_listen.clicked.connect(self.start_listening)
        self.btn_stop.clicked.connect(self.stop_speaking)
        self.btn_close.clicked.connect(self.fade_out)
        self.on_state(IDLE)

    # ---- reacting to real events ---------------------------------------
    def on_state(self, state):
        self.orb.set_state(state)
        self.status.setText(STATUS_TEXT.get(state, state))
        self.btn_listen.setVisible(state in (IDLE, ERROR))
        self.btn_stop.setVisible(state == SPEAKING)
        if state != IDLE:
            self.present()
        if state in HIDE_AFTER_MS:
            if self.isVisible():
                self._hide_timer.start(HIDE_AFTER_MS[state])
        else:
            self._hide_timer.stop()

    def on_caption(self, text):
        self.caption.setText(text)

    def on_failed(self, reason):
        self.caption.setText((reason or "").splitlines()[0][:90] if reason else "")

    # ---- showing and hiding --------------------------------------------
    def present(self):
        if self.isVisible():
            return
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.center().x() - self.width() // 2, screen.bottom() - self.height() - 40)
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self._fade(0.0, 1.0, 320)

    def fade_out(self):
        if not self.isVisible():
            return
        self._fade(self.windowOpacity(), 0.0, 400, then=self._finish_hide)

    def _finish_hide(self):
        self.hide()
        self.caption.setText("")

    def _fade(self, start, end, ms, then=None):
        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(ms)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        if then is not None:
            anim.finished.connect(then)
        anim.start()
        self._anim = anim

    # ---- user actions --------------------------------------------------
    def start_listening(self):
        if self._busy:
            return
        self._busy = True
        self.present()   # no "Listening" here: the bridge emits it when audio really flows
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        quit_ = False
        try:
            quit_ = self.bridge.listen_and_handle()
        except Exception as exc:
            self.bus.task_failed.emit("Listening failed: %s" % exc)
        finally:
            self._busy = False
        if quit_:
            self.quit_requested.emit()

    def stop_speaking(self):
        self.bridge.speaker.stop()
