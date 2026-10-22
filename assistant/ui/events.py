"""Qt signal bus for the floating UI. Needs PySide6."""
from PySide6.QtCore import QObject, Signal
from assistant.ui.states import EVENT_NAMES, IDLE, next_state

class EventBus(QObject):
    wake_detected = Signal()
    listening_started = Signal()
    audio_level = Signal(float)
    transcript_updated = Signal(str, bool)
    processing_started = Signal()
    speaking_started = Signal()
    speaking_finished = Signal()
    task_completed = Signal()
    task_failed = Signal(str)
    task_cancelled = Signal()
    caption_changed = Signal(str)
    state_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.state = IDLE
        for name in EVENT_NAMES:
            getattr(self, name).connect(lambda *args, n=name: self._on(n))

    def _on(self, name):
        new = next_state(self.state, name)
        if new != self.state:
            self.state = new
            self.state_changed.emit(new)

# Provide BUS instance for new brain code
BUS = EventBus()
