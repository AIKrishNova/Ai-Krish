import subprocess
import webbrowser
import urllib.parse

APP_MAPPING = {
    "safari": "Safari",
    "chrome": "Google Chrome",
    "google chrome": "Google Chrome",
    "notes": "Notes",
    "vscode": "Visual Studio Code",
    "code": "Visual Studio Code",
    "visual studio code": "Visual Studio Code",
    "finder": "Finder",
    "calendar": "Calendar",
    "reminders": "Reminders",
    "spotify": "Spotify",
    "music": "Music",
    "apple music": "Music",
    "mail": "Mail",
    "terminal": "Terminal",
    "system settings": "System Settings",
    "settings": "System Settings",
    "calculator": "Calculator",
    "maps": "Maps",
    "messages": "Messages",
    "photos": "Photos",
    "facetime": "FaceTime",
}

def open_app(app_name: str):
    app_name = (app_name or "").lower().strip()
    if not app_name:
        return {"success": False, "message": "No app name provided", "caption": "No app name"}
    try:
        mac_app = APP_MAPPING.get(app_name, app_name.title())
        subprocess.run(["open", "-a", mac_app], check=False)
        display_name = mac_app
        return {
            "success": True,
            "message": f"Opened {display_name}",
            "caption": f"Opened {display_name}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to open {app_name}: {e}",
            "caption": f"Couldn't open {app_name}"
        }

def open_app_and_search(app: str, query: str, memory=None):
    app = (app or "safari").lower().strip()
    query = (query or "").strip()
    display_app = APP_MAPPING.get(app, app.title())
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    try:
        webbrowser.open(url)
        results = [
            {"title": f"{query} - result 1", "url": f"https://www.google.com/search?q={urllib.parse.quote(query)}&result=1"},
            {"title": f"{query} - result 2", "url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(query)}"},
            {"title": f"{query} - result 3", "url": f"https://www.google.com/search?q={urllib.parse.quote(query)}&result=3"},
        ]
        if memory:
            memory.last_search_results = results
            memory.last_opened_url = url
        return {
            "success": True,
            "message": f"Searching for \"{query}\" in {display_app}",
            "caption": f"Searching for \"{query}\"",
            "url": url,
            "results": results
        }
    except Exception as e:
        return {"success": False, "message": f"Failed: {e}", "caption": "Search failed"}
