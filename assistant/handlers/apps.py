import subprocess
import webbrowser
import urllib.parse

def open_app(app_name):
    app_name = app_name.lower().strip()
    if not app_name:
        return {"success": False, "message": "No app name"}
    try:
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

def open_app_and_search(app, query, memory=None):
    app = app.lower().strip() if app else "safari"
    query = query or ""
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    try:
        webbrowser.open(url)
        # Save for reference resolution
        results = [
            {"title": f"{query} - result 1", "url": f"https://www.google.com/search?q={query}&result=1"},
            {"title": f"{query} - result 2", "url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(query)}"},
            {"title": f"{query} - result 3", "url": f"https://www.google.com/search?q={query}&result=3"},
        ]
        if memory:
            memory.last_search_results = results
            memory.last_opened_url = url
        return {"success": True, "message": f"Done! I opened {app} and searched for {query}", "url": url, "results": results}
    except Exception as e:
        return {"success": False, "message": f"Failed: {e}"}
