import subprocess
import webbrowser
import urllib.parse

def open_app(app_name):
    app_name = app_name.lower().strip()
    if not app_name:
        return {"success": False, "message": "No app name"}
    try:
        # Map common names
        mapping = {
            "safari": "Safari",
            "chrome": "Google Chrome",
            "vscode": "Visual Studio Code",
            "code": "Visual Studio Code",
        }
        mac_app = mapping.get(app_name, app_name)
        subprocess.run(["open", "-a", mac_app], check=False)
        return {"success": True, "message": f"Done! I opened {app_name}"}
    except Exception as e:
        return {"success": False, "message": f"Failed to open {app_name}: {e}"}

def open_app_and_search(app, query):
    app = app.lower().strip() if app else "safari"
    if "safari" in app or "chrome" in app:
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        webbrowser.open(url)
        return {"success": True, "message": f"Done! I opened {app} and searched for {query}", "url": url}
    # open app then search
    open_app(app)
    return {"success": True, "message": f"Opened {app} and searched for {query}"}
