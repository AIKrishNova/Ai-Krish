"""Floating assistant.  Run:  python -m assistant.ui   (add --demo to preview the animation)"""
import sys
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from assistant.ui.bridge import build_default
from assistant.ui.events import EventBus
from assistant.ui.main_window import SiriWindow

def main():
    app = QApplication(sys.argv)
    bus = EventBus()
    bridge = build_default(bus)
    window = SiriWindow(bus, bridge)
    window.quit_requested.connect(app.quit)
    app.aboutToQuit.connect(bridge.stop)
    if "--demo" in sys.argv:
        steps = [
            (300, bus.wake_detected.emit),
            (1200, bus.listening_started.emit),
            (1300, lambda: [bus.audio_level.emit(v / 10.0) for v in (2, 5, 8, 6, 9)]),
            (3000, bus.processing_started.emit),
            (4500, bus.speaking_started.emit),
            (6000, bus.speaking_finished.emit),
            (6100, bus.task_completed.emit),
        ]
        for ms, fn in steps:
            QTimer.singleShot(ms, fn)
    else:
        window.start_listening()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
