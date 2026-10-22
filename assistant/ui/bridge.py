"""Connects the real assistant to the UI events. No Qt in this file."""
import time

from assistant.reminders import handle_reminder_command
from assistant.speech import handle_speech_command

# Router replies that mean "this did not work".
FAILURE_MARKERS = (
    "not on my approved list",
    "i don't know that command",
    "the system reported an error",
    "sorry, something went wrong",
)
LEVEL_FULL_SCALE = 0.05   # microphone level that fills the orb


def short_caption(text, limit=60):
    lines = (text or "").strip().splitlines()
    line = lines[0].strip() if lines else ""
    return line if len(line) <= limit else line[: limit - 1].rstrip() + "\u2026"


def speaker_busy(speaker):
    proc = getattr(speaker, "_proc", None)
    return proc is not None and proc.poll() is None


class Bridge:
    def __init__(self, bus, router, speaker, listener, reminders=None,
                 poll_interval=0.1, max_speech_seconds=60):
        self.bus = bus
        self.router = router
        self.speaker = speaker
        self.listener = listener
        self.reminders = reminders
        self.poll_interval = poll_interval
        self.max_speech_seconds = max_speech_seconds

    # ---- typed or heard text -------------------------------------------
    def handle_text(self, text):
        """Run one command. Returns True if the assistant should quit."""
        bus = self.bus
        bus.processing_started.emit()
        try:
            reply, quit_, failed, speak_it = self._run(text)
        except Exception as exc:
            bus.task_failed.emit("Something went wrong: %s" % exc)
            return False
        bus.caption_changed.emit(short_caption(reply))
        if failed:
            bus.task_failed.emit(reply)
            return False
        if speak_it and self._speak(reply):
            pass
        bus.task_completed.emit()
        return quit_

    def _run(self, text):
        handled = handle_speech_command(text, self.speaker)
        if handled is not None:
            reply, say_it = handled
            self.router.pending = None
            return reply, False, False, say_it
        if self.reminders is not None:
            reply = handle_reminder_command(text, self.reminders)
            if reply is not None:
                return reply, False, False, True
        result = self.router.handle(text)
        failed = any(m in result.text.lower() for m in FAILURE_MARKERS)
        return result.text, result.quit, failed, not result.quit

    def _speak(self, reply):
        if not self.speaker.speak(reply):
            return False          # speech is off or could not start: no animation
        self.bus.speaking_started.emit()
        deadline = time.time() + self.max_speech_seconds
        while speaker_busy(self.speaker) and time.time() < deadline:
            time.sleep(self.poll_interval)
        self.bus.speaking_finished.emit()
        return True

    # ---- voice ----------------------------------------------------------
    def listen_and_handle(self):
        bus = self.bus
        self.router.pending = None   # a voice request can never answer a waiting yes/no
        self.speaker.stop()
        started = False

        def on_level(level):
            nonlocal started
            if not started:
                started = True
                bus.listening_started.emit()   # first real audio block from the mic
            bus.audio_level.emit(max(0.0, min(1.0, level / LEVEL_FULL_SCALE)))

        def show(message):
            bus.caption_changed.emit(short_caption(message))
            if "microphone is off" in message.lower():
                bus.processing_started.emit()  # transcription starts now

        try:
            result = self.listener.listen_once(show, on_level=on_level)
        except Exception as exc:
            bus.task_failed.emit("Listening failed: %s" % exc)
            return False
        if result.text is None:
            reason = ((result.error or "Listening failed").splitlines() or [""])[0]
            if reason.startswith("Cancelled"):
                bus.task_cancelled.emit()
            else:
                bus.caption_changed.emit(short_caption(reason))
                bus.task_failed.emit(reason)
            return False
        bus.transcript_updated.emit(result.text, True)
        return self.handle_text(result.text)

    # ---- background reminders ------------------------------------------
    def on_reminder(self, message):
        self.bus.caption_changed.emit(short_caption(message))
        self.speaker.speak(message)

    def stop(self):
        if self.reminders is not None:
            self.reminders.stop()
        self.speaker.stop()


def build_default(bus):
    """Build the bridge from the real assistant parts."""
    from assistant.commands import Router
    from assistant.config import db_path
    from assistant.desktop import Desktop
    from assistant.listen import Listener
    from assistant.reminders import Reminders
    from assistant.speech import Speaker
    from assistant.storage import NoteStore

    bridge = Bridge(bus, Router(NoteStore(db_path()), Desktop()), Speaker(), Listener())
    bridge.reminders = Reminders(bridge.on_reminder)
    return bridge
