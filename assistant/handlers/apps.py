import subprocess
ALLOWED={"safari":"Safari","chrome":"Google Chrome","notes":"Notes","【entity-spotify¦canonical_name=Spotify】":"【entity-Spotify¦canonical_name=Spotify】","finder":"Finder","calendar":"Calendar","reminders":"Reminders"}
def open_app(app_name):
    real=ALLOWED.get(app_name.lower(), app_name.capitalize())
    try:
        subprocess.run(["open","-a",real], check=True, timeout=5)
        return {"success": True, "app": real, "message": f"Opened {real}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
def open_app_and_search(app, query):
    res=open_app(app)
    if not res["success"]: return res
    import urllib.parse; q=urllib.parse.quote(query); url=f"https://www.google.com/search?q={q}"
    try:
        subprocess.run(["open", url], timeout=5)
        return {"success": True, "app": app, "query": query, "url": url, "results": [{"title":f"Search {query}","url":url}], "message": f"Done! I opened {app} and searched for {query}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
