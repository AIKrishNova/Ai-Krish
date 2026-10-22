"""Spoken replies (text-to-speech) for Mac and Windows. Off by default."""
import os
import re
import subprocess

from assistant import config
from assistant.commands import WAKE

MAX_SPOKEN_CHARS = 300


def clean_for_speech(text, limit=MAX_SPOKEN_CHARS):
    """Make a reply pleasant to hear: no links, no symbols, not too long."""
    t = re.sub(r"https?://\S+", "link", text or "")
    t = re.sub(r"[*#`_>|]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) > limit:
        t = t[:limit].rsplit(" ", 1)[0].rstrip(",;:") + "."
    return t


class Speaker:
    def __init__(self, platform=None, popen=None, enabled=False):
        self.platform = platform or config.detect_platform()
        self._popen = popen or subprocess.Popen
        self.enabled = enabled
        self._proc = None

    def supported(self):
        return self.platform in ("mac", "windows")

    def _build(self, text):
        # A leading dash could be mistaken for an option by the 'say' command.
        text = text.lstrip("-").strip()
        if not text:
            return None
        if self.platform == "mac":
            return ["say", "-r", "185", text], None
        if self.platform == "windows":
            script = (
                "Add-Type -AssemblyName System.Speech;"
                "(New-Object System.Speech.Synthesis.SpeechSynthesizer)"
                ".Speak($env:AIKRISH_SPEECH_TEXT)"
            )
            env = dict(os.environ, AIKRISH_SPEECH_TEXT=text)
            return ["powershell", "-NoProfile", "-Command", script], env
        return None

    def speak(self, text):
        """Speak text if speech is on. Returns True if speech was started."""
        if not self.enabled:
            return False
        built = self._build(clean_for_speech(text))
        if built is None:
            return False
        args, env = built
        self.stop()
        try:
            self._proc = self._popen(
                args, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except OSError:
            self._proc = None
            return False
        return True

    def stop(self):
        proc, self._proc = self._proc, None
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
            except OSError:
                pass


_ON = re.compile(r"(?:speak|voice|speech)\s+on", re.IGNORECASE)
_OFF = re.compile(r"(?:speak|voice|speech)\s+off", re.IGNORECASE)
_STOP = re.compile(r"stop\s+(?:speaking|talking)|stop|be\s+quiet", re.IGNORECASE)


def handle_speech_command(raw, speaker):
    """Handle speak on / speak off / stop speaking.

    Returns (reply_text, should_speak_reply), or None if this is not a speech command.
    """
    text = WAKE.sub("", (raw or "").strip(), count=1).strip().rstrip(".!?").strip()
    if _ON.fullmatch(text):
        if not speaker.supported():
            return ("Spoken replies are only supported on Mac and Windows.", False)
        speaker.enabled = True
        return (
            "Spoken replies are on. Type 'speak off' to turn them off, "
            "or 'stop speaking' to cut me off.",
            True,
        )
    if _OFF.fullmatch(text):
        speaker.enabled = False
        speaker.stop()
        return ("Spoken replies are off.", False)
    if _STOP.fullmatch(text):
        speaker.stop()
        return ("Stopped speaking.", False)
    return None
