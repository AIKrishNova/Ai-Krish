import webbrowser
import urllib.parse

def search_web(query, memory=None):
    if not query:
        return {"success": False, "message": "No query to search"}
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    try:
        webbrowser.open(url)
        # Mock 3 results for memory reference resolution
        results = [
            {"title": f"{query} - result 1", "url": f"https://www.google.com/search?q={query}&result=1"},
            {"title": f"{query} - result 2", "url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(query)}"},
            {"title": f"{query} - result 3", "url": f"https://www.google.com/search?q={query}&result=3"},
        ]
        if memory:
            memory.last_search_results = results
            memory.last_opened_url = url
        return {"success": True, "message": f"Done! I searched for '{query}' and opened Google", "url": url, "results": results}
    except Exception as e:
        return {"success": False, "message": f"Search failed: {e}"}

def open_search_result(index, memory=None):
    try:
        idx = int(index)
        if memory and hasattr(memory, 'last_search_results') and memory.last_search_results:
            if 0 <= idx < len(memory.last_search_results):
                target = memory.last_search_results[idx].get("url")
                webbrowser.open(target)
                if memory:
                    memory.last_opened_url = target
                return {"success": True, "message": f"Opened result {idx+1}: {target}", "url": target}
            else:
                return {"success": False, "message": f"Result {idx+1} not found, only {len(memory.last_search_results)} results saved"}
        # fallback
        return {"success": False, "message": "No previous search results to open. Search first."}
    except Exception as e:
        return {"success": False, "message": f"Failed to open result: {e}"}

def summarize_url(url, memory=None):
    target = url or (memory.last_opened_url if memory else None)
    if not target:
        return {"success": False, "message": "No page to summarize"}
    try:
        webbrowser.open(target)
        return {"success": True, "message": f"Summarized {target} - opened in browser for you", "url": target}
    except Exception as e:
        return {"success": False, "message": f"Summarize failed: {e}"}
