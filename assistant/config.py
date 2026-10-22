"""Settings for the AI Krish assistant.

Edit APPS, SITES and FOLDERS to change what the assistant may open.
Anything not on these lists is refused.
"""
import os
import sys
from pathlib import Path


def detect_platform():
    if sys.platform == "darwin":
        return "mac"
    if sys.platform.startswith("win"):
        return "windows"
    return "other"


def data_dir():
    """Where notes are stored. It is outside the project, so Git never sees it.
    Change it by setting the AIKRISH_DATA_DIR environment variable."""
    override = os.environ.get("AIKRISH_DATA_DIR")
    base = Path(override).expanduser() if override else Path.home() / ".ai-krish"
    base.mkdir(parents=True, exist_ok=True)
    return base


def db_path():
    return data_dir() / "assistant.db"


# friendly name -> real app name on each system
APPS = {
    "safari": {"mac": "Safari"},
    "chrome": {"mac": "Google Chrome", "windows": "chrome"},
    "terminal": {"mac": "Terminal"},
    "textedit": {"mac": "TextEdit"},
    "apple notes": {"mac": "Notes"},
    "calculator": {"mac": "Calculator", "windows": "calc"},
    "notepad": {"windows": "notepad"},
    "paint": {"windows": "mspaint"},
    "spotify": {"mac": "Spotify", "windows": "spotify"},
    "whatsapp": {"mac": "WhatsApp", "windows": "whatsapp"},
    "finder": {"mac": "Finder"},
    "vscode": {"mac": "Visual Studio Code", "windows": "code"},
}

SITES = {
    "gmail": "https://mail.google.com",
    "youtube": "https://www.youtube.com",
    "github": "https://github.com",
    "chatgpt": "https://chatgpt.com",
    "google": "https://www.google.com",
    "whatsapp web": "https://web.whatsapp.com",
    "spotify web": "https://open.spotify.com",
}

# friendly name -> folder inside your home folder
FOLDERS = {
    "desktop": "Desktop",
    "documents": "Documents",
    "downloads": "Downloads",
}
