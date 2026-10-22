"""Tiny event bus. The assistant emits real events; a UI (or a test) listens."""
import threading

EVENTS = (
    "wake_detected", "listening_started", "transcript_updated",
    "processing_started", "speaking_started", "speaking_finished",
    "task_completed", "task_failed", "task_cancelled",
)


class EventBus:
    def __init__(self):
        self._lock = threading.Lock()
        self._listeners = []

    def subscribe(self, callback):
        with self._lock:
            self._listeners.append(callback)

    def emit(self, name, **data):
        if name not in EVENTS:
            raise ValueError("unknown event: %s" % name)
        with self._lock:
            listeners = list(self._listeners)
        for callback in listeners:
            try:
                callback(name, data)
            except Exception:
                pass  # a broken listener must never break the assistant


BUS = EventBus()
