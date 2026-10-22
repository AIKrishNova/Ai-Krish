from .events import BUS
from ..commands import Router
from ..config import db_path
from ..desktop import Desktop
from ..storage import NoteStore
from ..speech import Speaker
from ..listen import Listener

class UIBridge:
    def __init__(self):
        self.router = Router(NoteStore(db_path()), Desktop())
        self.speaker = Speaker()
        self.listener = Listener()
        BUS.audio_level.connect(self.on_audio)

    def on_audio(self, lvl):
        pass # orb handles it

    def handle_text(self, text: str):
        if not text or not text.strip():
            BUS.task_failed.emit("Didn't catch that")
            return
        BUS.processing_started.emit()
        BUS.transcript_updated.emit(text, True)
        try:
            reply = self.router.handle(text)
            if reply.quit:
                BUS.task_cancelled.emit()
                return
            low = reply.text.lower()
            if "not on my approved list" in low or "is not supported" in low or "is not on my" in low:
                BUS.task_failed.emit(reply.text)
                return
            BUS.speaking_started.emit(reply.text)
            BUS.task_completed.emit(reply.text)
            self.speaker.speak(reply.text)
            BUS.speaking_finished.emit()
        except Exception as ex:
            BUS.task_failed.emit(str(ex))
