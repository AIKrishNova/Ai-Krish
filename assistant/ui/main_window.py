"""Native macOS Siri-like floating window with frosted glass and glowing orb."""
import sys
import threading
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from .events import EventBus
from .bridge import build_default, short_caption
from .orb_widget import OrbWidget
from .states import IDLE, LISTENING, THINKING, SPEAKING, ERROR, WAKE

STATUS_TEXT = {
    IDLE: "Ready",
    WAKE: "Waking\u2026",
    LISTENING: "Listening\u2026",
    THINKING: "Thinking\u2026",
    SPEAKING: "Speaking\u2026",
    ERROR: "Something went wrong",
}


class SiriWindow(QWidget):
    quit_requested = Signal()

    def __init__(self, bus=None, bridge=None):
        super().__init__()
        self.bus = bus or EventBus()
        self.bridge = bridge or build_default(self.bus)
        self._fade_anim = None
        self._drag_pos = None

        # Frameless, translucent, floating tool window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setFixedSize(360, 410)

        # Frosted glass background card
        self.glass = QWidget(self)
        self.glass.setGeometry(10, 10, 340, 390)
        self.glass.setStyleSheet("""
            QWidget {
                background: rgba(26, 26, 34, 0.72);
                border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 32px;
            }
        """)

        layout = QVBoxLayout(self.glass)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)

        # Status Pill at top
        self.status = QLabel(STATUS_TEXT[IDLE])
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 0.14);
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: 16px;
                padding: 6px 18px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 600;
                letter-spacing: 0.3px;
            }
        """)

        # Close button in top right
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 14px;
                color: rgba(255, 255, 255, 0.7);
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.22);
                color: #ffffff;
            }
        """)
        close_btn.clicked.connect(self.close_and_quit)

        top_row = QHBoxLayout()
        top_row.addSpacing(28)  # Visual balance for the close button
        top_row.addStretch()
        top_row.addWidget(self.status)
        top_row.addStretch()
        top_row.addWidget(close_btn)
        layout.addLayout(top_row)

        layout.addStretch()

        # Orb Widget in center
        self.orb_widget = OrbWidget()
        layout.addWidget(self.orb_widget, alignment=Qt.AlignCenter)

        layout.addStretch()

        # Caption label for assistant responses
        self.caption = QLabel("")
        self.caption.setAlignment(Qt.AlignCenter)
        self.caption.setWordWrap(True)
        self.caption.setStyleSheet("""
            QLabel {
                background: transparent;
                color: rgba(255, 255, 255, 0.92);
                font-size: 13px;
                padding: 2px 8px;
                min-height: 20px;
            }
        """)
        layout.addWidget(self.caption, alignment=Qt.AlignCenter)

        # Action Buttons: Listen (◉), Stop (■), Cancel (✕)
        btn_style = """
            QPushButton {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 18px;
                color: rgba(255, 255, 255, 0.9);
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.22);
                color: #ffffff;
            }
        """
        self.btn_listen = QPushButton("◉")
        self.btn_stop = QPushButton("■")
        self.btn_cancel = QPushButton("✕")
        self.btn_listen.setToolTip("Start Listening")
        self.btn_stop.setToolTip("Stop")
        self.btn_cancel.setToolTip("Cancel")

        for btn in (self.btn_listen, self.btn_stop, self.btn_cancel):
            btn.setStyleSheet(btn_style)
            btn.setFixedSize(42, 36)

        self.btn_listen.clicked.connect(self.start_listening)
        self.btn_stop.clicked.connect(self.stop_all)
        self.btn_cancel.clicked.connect(self.close)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(self.btn_listen)
        btn_row.addWidget(self.btn_stop)
        btn_row.addWidget(self.btn_cancel)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Wire EventBus signals
        self.bus.caption_changed.connect(self.set_caption)
        self.bus.transcript_updated.connect(lambda t, f: self.set_caption(t))
        self.bus.wake_detected.connect(self.on_wake)
        self.bus.listening_started.connect(lambda: self.set_state(LISTENING))
        self.bus.audio_level.connect(self.orb_widget.set_level)
        self.bus.processing_started.connect(lambda: self.set_state(THINKING))
        self.bus.speaking_started.connect(lambda: self.set_state(SPEAKING))
        self.bus.task_completed.connect(self._on_task_completed)
        self.bus.task_failed.connect(self._on_task_failed)
        self.bus.task_cancelled.connect(self._on_task_cancelled)

        # Keyboard shortcuts
        QShortcut(QKeySequence(Qt.Key_Escape), self, self.close)

        # Setup global Option+Space hotkey via pynput
        self._init_global_hotkey()

        # Start hidden per test_starts_idle_and_hidden
        self.hide()

    def _init_global_hotkey(self):
        import os
        if os.environ.get("QT_QPA_PLATFORM") == "offscreen" or os.environ.get("AI_KRISH_NO_HOTKEY"):
            return
        try:
            from pynput import keyboard
            def on_hotkey():
                # Runs on pynput background thread, safely emits Qt signal
                self.bus.wake_detected.emit()

            self._hotkey_listener = keyboard.GlobalHotKeys({
                '<alt>+<space>': on_hotkey
            })
            self._hotkey_listener.daemon = True
            self._hotkey_listener.start()
            print("[Hotkey] Option+Space global hotkey active")
        except Exception as e:
            print(f"[Hotkey] Note: global hotkey unavailable ({e})")

    def on_wake(self):
        if self.isVisible():
            self.raise_()
            self.activateWindow()
            self.start_listening()
            return

        self._position_top_right()
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self.activateWindow()

        # Smooth fade-in animation
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade_anim.setDuration(280)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._fade_anim.start()

        self.start_listening()

    def _position_top_right(self):
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            x = geom.right() - self.width() - 28
            y = geom.top() + 36
            self.move(x, y)

    def set_state(self, state):
        self.status.setText(STATUS_TEXT.get(state, str(state)))
        try:
            self.orb_widget.set_state(state)
        except Exception:
            pass

        show_active = state in (LISTENING, THINKING, SPEAKING)
        self.btn_stop.setVisible(show_active)
        self.btn_cancel.setVisible(show_active)

    def set_caption(self, text):
        self.caption.setText(short_caption(text, limit=120))

    def _on_task_completed(self):
        self.set_state(IDLE)
        QTimer.singleShot(2600, self._auto_fade_out)

    def _on_task_failed(self, msg=""):
        self.set_state(ERROR)
        if msg:
            self.set_caption(msg)
        QTimer.singleShot(3500, self._auto_fade_out)

    def _on_task_cancelled(self):
        self.set_state(IDLE)
        self.close()

    def _auto_fade_out(self):
        if self.isVisible() and self.status.text() in (STATUS_TEXT[IDLE], STATUS_TEXT[ERROR]):
            self._fade_anim = QPropertyAnimation(self, b"windowOpacity", self)
            self._fade_anim.setDuration(350)
            self._fade_anim.setStartValue(self.windowOpacity())
            self._fade_anim.setEndValue(0.0)
            self._fade_anim.setEasingCurve(QEasingCurve.InCubic)
            self._fade_anim.finished.connect(self.close)
            self._fade_anim.start()

    def start_listening(self):
        print("[Window] Orb shown - starting listener")
        if hasattr(self.bridge, 'listen_and_handle'):
            def run():
                self.bridge.listen_and_handle()
            threading.Thread(target=run, daemon=True).start()
        elif hasattr(self.bridge, 'listener') and self.bridge.listener:
            self.bridge.listener.start()
        elif hasattr(self.bridge, 'handle_text'):
            self.bridge.handle_text("hello")

    def stop_all(self):
        if hasattr(self.bridge, 'stop'):
            self.bridge.stop()
        elif hasattr(self.bridge, 'speaker') and hasattr(self.bridge.speaker, 'stop'):
            self.bridge.speaker.stop()
        self.bus.task_cancelled.emit()

    def close_and_quit(self):
        self.stop_all()
        self.quit_requested.emit()
        QApplication.instance().quit()
        self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    bus = EventBus()
    bridge = build_default(bus)
    win = SiriWindow(bus, bridge)
    win.show()
    win.start_listening()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
