
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, QTimer
from .events import EventBus
from .bridge import build_default
from .orb_widget import OrbWidget
from .states import OrbState

class SiriWindow(QObject):
    def __init__(self, bus=None):
        super().__init__()
        self.bus = bus or EventBus()
        self.bridge = build_default(self.bus)
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.orb = OrbWidget(self.bus)
        self.orb.show()
        self.bus.caption_changed.connect(self.orb.set_caption)
        self.bus.listening_started.connect(lambda: self.orb.set_state(OrbState.LISTENING))
        self.bus.processing_started.connect(lambda: self.orb.set_state(OrbState.PROCESSING))
        self.bus.speaking_started.connect(lambda: self.orb.set_state(OrbState.SPEAKING))
        self.bus.task_completed.connect(lambda: self.orb.set_state(OrbState.IDLE))
        self.bus.task_failed.connect(lambda m: self.orb.set_state(OrbState.ERROR))

    def start_listening(self):
        print("[Window] Orb shown - starting listener")
        if hasattr(self.bridge, 'listener') and self.bridge.listener:
            self.bridge.listener.start()
        self.bridge.handle_text("hello")
        return self.app.exec()

    def stop(self):
        print("[Window] stop")
        if hasattr(self.bridge, 'listener') and self.bridge.listener:
            self.bridge.listener.stop()
        self.bridge.stop()
        self.orb.close()
        self.app.quit()

def main():
    bus = EventBus()
    window = SiriWindow(bus)
    sys.exit(window.start_listening())

if __name__ == "__main__":
    main()
