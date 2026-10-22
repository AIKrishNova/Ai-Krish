from PySide6.QtCore import QObject, Signal

class Bus(QObject):
    wake_detected = Signal()
    listening_started = Signal()
    audio_level = Signal(float)
    transcript_updated = Signal(str, bool)
    processing_started = Signal()
    speaking_started = Signal(str)
    speaking_finished = Signal()
    task_completed = Signal(str)
    task_failed = Signal(str)
    task_cancelled = Signal()

BUS = Bus()
