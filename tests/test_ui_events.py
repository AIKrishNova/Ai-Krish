import unittest

try:
    from assistant.ui.events import EventBus
except ImportError:  # PySide6 is only in the venv
    EventBus = None


@unittest.skipIf(EventBus is None, "PySide6 not installed in this Python")
class EventBusTests(unittest.TestCase):
    def setUp(self):
        self.bus = EventBus()
        self.states = []
        self.bus.state_changed.connect(self.states.append)

    def test_flow_emits_state_changes(self):
        self.bus.listening_started.emit()
        self.bus.processing_started.emit()
        self.bus.speaking_started.emit()
        self.bus.task_completed.emit()
        self.assertEqual(self.states, ["listening", "thinking", "speaking", "idle"])

    def test_failure_sets_error(self):
        self.bus.processing_started.emit()
        self.bus.task_failed.emit("not on my approved list")
        self.assertEqual(self.bus.state, "error")

    def test_audio_level_does_not_change_state(self):
        self.bus.audio_level.emit(0.5)
        self.assertEqual(self.states, [])


if __name__ == "__main__":
    unittest.main()
