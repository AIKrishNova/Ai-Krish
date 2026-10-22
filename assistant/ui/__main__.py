from PySide6.QtWidgets import QApplication
import sys
from .main_window import SiriWindow
from .events import BUS

def main():
    app = QApplication(sys.argv)
    win = SiriWindow()
    if "--test-events" in sys.argv:
        win.show()
        from PySide6.QtCore import QTimer
        seq = [
            (500, lambda: BUS.wake_detected.emit()),
            (1500, lambda: BUS.listening_started.emit()),
            (2000, lambda: [BUS.audio_level.emit(v/10) for v in [2,5,8,6,9]]),
            (3000, lambda: BUS.processing_started.emit()),
            (4500, lambda: BUS.speaking_started.emit("Opened Safari")),
            (6000, lambda: BUS.task_completed.emit("Done")),
        ]
        for ms, fn in seq:
            QTimer.singleShot(ms, fn)
    elif "--debug" in sys.argv:
        win.show()
    else:
        win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
