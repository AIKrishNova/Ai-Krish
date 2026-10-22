"""Push-to-talk voice input. Works only when the voice libraries are installed.

Nothing is recorded unless you type 'listen'. One request = one recording.
Audio is turned into text on this computer; it is not sent anywhere.
"""
import importlib
import os
import re
from dataclasses import dataclass
from typing import Optional

from assistant.commands import WAKE

SAMPLE_RATE = 16000
BLOCK = 1600  # 0.1 second of audio per block
DEFAULT_MODEL = "base.en"
# Words the assistant understands. Whisper uses this as a spelling hint only.
COMMAND_HINT = (
    "Open Safari. Open Gmail. Open Chrome. Open Finder. Open Downloads. "
    "Take a note. List notes. Copy latest note. Remind me in 10 minutes to call mom. "
    "Set a timer for 5 minutes. List reminders. Speak on. Speak off. Help."
)
VENV_HINT = "~/.ai-krish/venv/bin/python -m assistant"
MIC_HINT = (
    "Check that Terminal is allowed to use the microphone "
    "(System Settings > Privacy & Security > Microphone)."
)

# Phrases the speech model sometimes invents when it hears only silence.
_SILENCE_GHOSTS = {"you", "thank you", "thanks for watching", "bye"}


class Endpointer:
    """Decides when you have started and finished speaking.

    It only looks at loudness numbers, so it needs no audio libraries and can be tested.
    One block = 0.1 second.
    """

    CONTINUE = "continue"
    DONE = "done"
    NO_SPEECH = "no_speech"
    MAX_LENGTH = "max_length"

    def __init__(
        self,
        calibration_blocks=5,
        min_threshold=0.01,
        max_threshold=0.05,
        multiplier=3.0,
        silence_blocks=12,
        max_blocks=150,
        wait_blocks=70,
    ):
        self.calibration_blocks = calibration_blocks
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold
        self.multiplier = multiplier
        self.silence_blocks = silence_blocks
        self.max_blocks = max_blocks
        self.wait_blocks = wait_blocks
        self.threshold = None
        self.started = False
        self.blocks = 0
        self._noise = []
        self._silent = 0

    def feed(self, level):
        self.blocks += 1
        if self.threshold is None:
            self._noise.append(level)
            if len(self._noise) >= self.calibration_blocks:
                middle = sorted(self._noise)[len(self._noise) // 2]
                self.threshold = min(
                    max(self.min_threshold, middle * self.multiplier), self.max_threshold
                )
            return self.CONTINUE
        if level > self.threshold:
            self.started = True
            self._silent = 0
        elif self.started:
            self._silent += 1
        if self.blocks >= self.max_blocks:
            return self.MAX_LENGTH if self.started else self.NO_SPEECH
        if self.started and self._silent >= self.silence_blocks:
            return self.DONE
        if not self.started and self.blocks >= self.wait_blocks:
            return self.NO_SPEECH
        return self.CONTINUE


def clean_transcript(text):
    """Tidy the speech model's output. Returns '' if there is nothing real in it."""
    t = re.sub(r"\[[^\]]*\]|\([^)]*\)", " ", text or "")
    t = re.sub(r"\s+", " ", t).strip()
    if not re.search(r"\w", t):
        return ""
    if t.lower().rstrip(".!?, ") in _SILENCE_GHOSTS:
        return ""
    return t


_LISTEN = re.compile(r"(?:start\s+)?listen(?:ing)?(?:\s+to\s+me)?", re.IGNORECASE)
_STOP_LISTENING = re.compile(r"stop\s+listening", re.IGNORECASE)


def _plain(raw):
    return WAKE.sub("", (raw or "").strip(), count=1).strip().rstrip(".!?").strip()


def is_listen_command(raw):
    return _LISTEN.fullmatch(_plain(raw)) is not None


def is_stop_listening_command(raw):
    return _STOP_LISTENING.fullmatch(_plain(raw)) is not None


@dataclass
class ListenResult:
    text: Optional[str]
    error: Optional[str]


class Listener:
    def __init__(self, model_name=None, importer=None):
        self.model_name = model_name or os.environ.get("AIKRISH_WHISPER_MODEL", DEFAULT_MODEL)
        self._import = importer or importlib.import_module
        self._model = None

    def check_libraries(self):
        for name in ("numpy", "sounddevice", "faster_whisper"):
            try:
                self._import(name)
            except Exception:  # missing library, or a broken audio library
                return False, (
                    "Voice input needs the voice libraries. Start the assistant with:\n  %s"
                    % VENV_HINT
                )
        return True, ""

    def listen_once(self, show):
        """Record once, turn it into text. 'show' is a function that prints a message."""
        ok, why = self.check_libraries()
        if not ok:
            return ListenResult(None, why)
        try:
            import numpy as np
            import sounddevice as sd

            if self._model is None:
                show(
                    "Loading the speech model. The first time, it downloads "
                    "a model file (about 150 MB for base.en), so please wait..."
                )
                from faster_whisper import WhisperModel

                self._model = WhisperModel(self.model_name, device="cpu", compute_type="int8")
        except KeyboardInterrupt:
            return ListenResult(None, "Cancelled.")
        except Exception as exc:
            return ListenResult(None, "Could not load the speech model: %s" % exc)

        show("Listening... the microphone is ON. Speak now, then pause. (Ctrl+C cancels)")
        frames = []
        endpointer = Endpointer()
        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE, channels=1, dtype="float32", blocksize=BLOCK
            ) as stream:
                while True:
                    data, _overflow = stream.read(BLOCK)
                    frames.append(data.copy())
                    level = float(np.sqrt(np.mean(data ** 2)))
                    if endpointer.feed(level) != Endpointer.CONTINUE:
                        break
        except KeyboardInterrupt:
            show("Microphone is OFF.")
            return ListenResult(None, "Cancelled.")
        except Exception as exc:
            return ListenResult(None, "Could not use the microphone: %s\n%s" % (exc, MIC_HINT))
        show("Microphone is OFF.")

        if not endpointer.started:
            return ListenResult(None, "I did not hear anything. " + MIC_HINT)
        try:
            audio = np.concatenate(frames).reshape(-1).astype("float32")
            segments, _info = self._model.transcribe(
                audio,
                language="en",
                beam_size=1,
                condition_on_previous_text=False,
                initial_prompt=COMMAND_HINT,
            )
            text = clean_transcript(" ".join(segment.text for segment in segments))
        except Exception as exc:
            return ListenResult(None, "Could not turn the speech into text: %s" % exc)
        if not text:
            return ListenResult(None, "I could not make out any words. Please try again.")
        return ListenResult(text, None)
