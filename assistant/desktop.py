"""Safe desktop actions for Mac and Windows.

Only allowlisted apps, sites and folders are opened. Commands are built as
argument lists (never one shell string), so typed text is never run as a
shell command.
"""
import os
import subprocess
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from assistant import config


@dataclass
class Result:
    ok: bool
    message: str


def clean_name(name):
    key = (name or "").strip().lower()
    for prefix in ("the ", "my "):
        if key.startswith(prefix):
            key = key[len(prefix):]
    for suffix in (" app", " folder", " website", " site"):
        if key.endswith(suffix):
            key = key[: -len(suffix)]
    return key.strip()


class Desktop:
    def __init__(self, platform=None, runner=None, browser_open=None, home=None):
        self.platform = platform or config.detect_platform()
        self._runner = runner or subprocess.run
        self._browser_open = browser_open or webbrowser.open
        self.home = Path(home) if home else Path.home()

    def _run(self, args, input_bytes=None, env=None):
        try:
            proc = self._runner(
                args, input=input_bytes, capture_output=True, timeout=15, env=env
            )
        except FileNotFoundError:
            return Result(False, "That system command was not found on this computer.")
        except subprocess.TimeoutExpired:
            return Result(False, "The system did not respond in time.")
        except OSError as exc:
            return Result(False, "Could not run the command: %s" % exc)
        if proc.returncode != 0:
            return Result(
                False,
                "The system reported an error (code %s). The app may not be installed."
                % proc.returncode,
            )
        return Result(True, "")

    def open_app(self, name):
        key = clean_name(name)
        entry = config.APPS.get(key)
        if entry is None:
            return Result(False, "'%s' is not on my approved app list." % name)
        target = entry.get(self.platform)
        if target is None:
            return Result(False, "%s is not available on this computer." % key.title())
        if self.platform == "mac":
            args = ["open", "-a", target]
        elif self.platform == "windows":
            args = ["cmd", "/c", "start", "", target]
        else:
            return Result(False, "Opening apps is only supported on Mac and Windows.")
        result = self._run(args)
        if not result.ok:
            return result
        return Result(True, "Asked your computer to open %s." % target)

    def open_folder(self, name):
        key = clean_name(name)
        rel = config.FOLDERS.get(key)
        if rel is None:
            return Result(False, "'%s' is not on my approved folder list." % name)
        path = self.home / rel
        if not path.is_dir():
            return Result(False, "The folder %s does not exist." % path)
        if self.platform == "mac":
            args = ["open", str(path)]
        elif self.platform == "windows":
            args = ["explorer", str(path)]
        else:
            return Result(False, "Opening folders is only supported on Mac and Windows.")
        result = self._run(args)
        if not result.ok:
            return result
        return Result(True, "Asked your computer to open the %s folder." % key)

    def open_website(self, target):
        key = clean_name(target)
        url = config.SITES.get(key, (target or "").strip())
        parsed = urlparse(url)
        bad = (
            parsed.scheme not in ("http", "https")
            or not parsed.netloc
            or any(ch.isspace() for ch in url)
            or len(url) > 2000
        )
        if bad:
            return Result(False, "I only open normal web links that start with http:// or https://.")
        if not self._browser_open(url):
            return Result(False, "I could not open your browser.")
        return Result(True, "Asked your browser to open %s." % url)

    def copy_text(self, text):
        if not text or not text.strip():
            return Result(False, "There is nothing to copy.")
        if len(text) > 100000:
            return Result(False, "That text is too long to copy.")
        if self.platform == "mac":
            result = self._run(["pbcopy"], input_bytes=text.encode("utf-8"))
        elif self.platform == "windows":
            env = dict(os.environ, AIKRISH_TEXT=text)
            result = self._run(
                ["powershell", "-NoProfile", "-Command", "Set-Clipboard -Value $env:AIKRISH_TEXT"],
                env=env,
            )
        else:
            return Result(False, "The clipboard is only supported on Mac and Windows.")
        return result if not result.ok else Result(True, "Copied to the clipboard.")
