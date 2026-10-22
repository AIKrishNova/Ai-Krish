import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
    from assistant.ui.events import EventBus
    from assistant.ui.main_window import SiriWindow
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


class FakeSpeaker:
    def stop(self):
        pass


class FakeBridge:
    def __init__(self):
        self.speaker = FakeSpeaker()
        self.calls = 0

    def listen_and_handle(self):
        self.calls += 1
        return False


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
class WindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.bus = EventBus()
        self.bridge = FakeBridge()
        self.win = SiriWindow(self.bus, self.bridge)

    def test_starts_idle_and_hidden(self):
        self.assertEqual(self.win.status.text(), "Ready")
        self.assertFalse(self.win.isVisible())

    def test_listening_text_comes_only_from_the_event(self):
        self.win.start_listening()
        self.assertEqual(self.win.status.text(), "Ready")
        self.bus.listening_started.emit()
        self.assertEqual(self.win.status.text(), "Listening\u2026")

    def test_failure_shows_error_and_reason(self):
        self.bus.processing_started.emit()
        self.bus.task_failed.emit("not on my approved list")
        self.assertEqual(self.win.status.text(), "Something went wrong")
        self.assertIn("approved", self.win.caption.text())

    def test_completed_returns_to_ready(self):
        self.bus.speaking_started.emit()
        self.bus.task_completed.emit()
        self.assertEqual(self.win.status.text(), "Ready")


if __name__ == "__main__":
    unittest.main()
