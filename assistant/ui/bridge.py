"""Connects the assistant brain, intents, and audio to Qt UI events."""
import time
from ..conversation.memory import ConversationMemory
from ..intents.router import route
from ..handlers.apps import open_app, open_app_and_search
from ..handlers import browser as browser_handler
from ..handlers import conversation as conv_handler
from ..tasks.manager import TaskManager

FAILURE_MARKERS = (
    "not on my approved list",
    "i don't know that command",
    "the system reported an error",
    "sorry, something went wrong",
    "failed",
)
LEVEL_FULL_SCALE = 0.05


def short_caption(text, limit=60):
    lines = (text or "").strip().splitlines()
    line = lines[0].strip() if lines else ""
    return line if len(line) <= limit else line[: limit - 1].rstrip() + "\u2026"


def speaker_busy(speaker):
    proc = getattr(speaker, "_proc", None)
    return proc is not None and getattr(proc, "poll", lambda: 0)() is None


class Bridge:
    def __init__(self, bus=None, router=None, speaker=None, listener=None,
                 reminders=None, poll_interval=0.1, max_speech_seconds=60):
        self.bus = bus
        self.router = router
        self.speaker = speaker
        self.listener = listener
        self.reminders = reminders
        self.poll_interval = poll_interval
        self.max_speech_seconds = max_speech_seconds
        self.memory = ConversationMemory()
        self.task_mgr = TaskManager()

        # Lazy-load live audio components if not supplied
        if self.listener is None or self.speaker is None:
            try:
                from ..audio.transcriber import Transcriber
                from ..audio.tts import TTS
                from ..audio.listener import MicListener
                self.transcriber = Transcriber()
                self.tts = self.speaker if self.speaker is not None else TTS()
                if self.listener is None:
                    self.listener = MicListener(self.transcriber, self.tts, self, bus)
            except Exception as e:
                print(f"[Bridge] Audio components not available: {e}")
                if self.listener is None:
                    self.listener = None
                self.tts = self.speaker
        else:
            self.tts = speaker

    def handle_text(self, text: str, emit_processing: bool = True):
        if not text or not text.strip():
            if self.bus:
                self.bus.task_failed.emit("Empty input")
            return {"success": False, "message": "Empty"}

        if emit_processing and self.bus:
            self.bus.processing_started.emit()

        # Custom / Mock router execution (e.g. from unit tests)
        if self.router is not None:
            try:
                result = self.router.handle(text)
                reply_text = result.text if hasattr(result, "text") else str(result)
                quit_ = getattr(result, "quit", False)
                caption = short_caption(reply_text)
                if self.bus:
                    self.bus.caption_changed.emit(caption)

                failed = any(m in reply_text.lower() for m in FAILURE_MARKERS)
                if failed:
                    if self.bus:
                        self.bus.task_failed.emit(reply_text)
                    return False

                if self.speaker and hasattr(self.speaker, "speak"):
                    spoke = self.speaker.speak(reply_text)
                    if spoke and self.bus:
                        self.bus.speaking_started.emit()
                        deadline = time.time() + self.max_speech_seconds
                        while speaker_busy(self.speaker) and time.time() < deadline:
                            if self.poll_interval > 0:
                                time.sleep(self.poll_interval)
                            else:
                                break
                        self.bus.speaking_finished.emit()

                if self.bus:
                    self.bus.task_completed.emit()
                return quit_
            except Exception as exc:
                if self.bus:
                    self.bus.task_failed.emit(str(exc))
                return False

        # Modern Intent Router execution
        intent = route(text, self.memory)
        print(f"[Krish] Intent: {intent.name} {intent.slots}")

        if intent.name == "stop":
            self.task_mgr.cancel()
            result = conv_handler.handle_stop(text, self.memory)
            if self.bus:
                try: self.bus.task_cancelled.emit()
                except Exception: pass
        elif intent.name == "greet":
            result = conv_handler.handle_greet(text, self.memory)
        elif intent.name in ("casual", "unsupported"):
            result = conv_handler.handle_casual(text, self.memory) if intent.name == "casual" else conv_handler.handle_unsupported(text, self.memory)
        elif intent.name == "open_app":
            result = open_app(intent.slots.get("app", ""))
        elif intent.name == "open_app_and_search":
            result = open_app_and_search(intent.slots.get("app", "safari"), intent.slots.get("query", ""), self.memory)
        elif intent.name == "search_web":
            result = browser_handler.search_web(intent.slots.get("query", ""), self.memory)
        elif intent.name == "open_search_result":
            result = browser_handler.open_search_result(intent.slots.get("index", 0), self.memory)
        elif intent.name == "summarize":
            result = browser_handler.summarize_url(intent.slots.get("url"), self.memory)
        else:
            result = conv_handler.handle_unsupported(text, self.memory)

        self.memory.add("user", text, intent.name, None)
        self.memory.add("assistant", result.get("message", ""), intent.name, result)

        caption = result.get("caption") or result.get("message", "")
        caption = short_caption(caption)

        if self.bus:
            self.bus.caption_changed.emit(caption)
            if result.get("success"):
                if self.speaker and hasattr(self.speaker, "supported") and not self.speaker.supported():
                    pass
                else:
                    self.bus.speaking_started.emit()
                    self.bus.speaking_finished.emit()
                self.bus.task_completed.emit()
            else:
                self.bus.task_failed.emit(result.get("message", "Task failed"))

        print(f"[Krish] -> {result.get('message', '')}")
        if self.tts and hasattr(self.tts, "speak"):
            try: self.tts.speak(result.get('message', ''))
            except Exception: pass
        return result

    def listen_and_handle(self, text=None):
        if text:
            return self.handle_text(text)

        # Synchronous listener support (e.g. from unit tests)
        if self.listener and hasattr(self.listener, "listen_once"):
            if self.speaker and hasattr(self.speaker, "stop"):
                self.speaker.stop()
            started = False

            def on_level(level):
                nonlocal started
                if not started:
                    started = True
                    if self.bus:
                        self.bus.listening_started.emit()
                if self.bus:
                    self.bus.audio_level.emit(max(0.0, min(1.0, float(level) / LEVEL_FULL_SCALE)))

            def show(message):
                if self.bus:
                    self.bus.caption_changed.emit(short_caption(message))
                    if "microphone is off" in message.lower():
                        self.bus.processing_started.emit()

            try:
                res = self.listener.listen_once(show, on_level=on_level)
            except Exception as exc:
                if self.bus:
                    self.bus.task_failed.emit(f"Listening failed: {exc}")
                return False

            if not res or getattr(res, "text", None) is None:
                err = getattr(res, "error", None) or "I did not hear anything."
                if self.bus:
                    self.bus.caption_changed.emit(short_caption(err))
                    self.bus.task_failed.emit(err)
                return False

            if self.bus:
                self.bus.transcript_updated.emit(res.text, True)
            return self.handle_text(res.text, emit_processing=False)

        # Continuous background MicListener support
        if self.listener and not getattr(self.listener, "running", False):
            self.listener.start()
        return self.handle_text("hello")

    def start_listening(self):
        return self.listen_and_handle()

    def stop(self):
        print("[Bridge] stop called")
        if self.listener and hasattr(self.listener, "stop"):
            self.listener.stop()
        if self.speaker and hasattr(self.speaker, "stop"):
            self.speaker.stop()
        if self.reminders and hasattr(self.reminders, "stop"):
            self.reminders.stop()
        self.task_mgr.cancel()
        if self.bus:
            try: self.bus.task_cancelled.emit()
            except Exception: pass


def build_default(bus=None):
    from .events import EventBus
    if bus is None:
        bus = EventBus()
    return Bridge(bus)
