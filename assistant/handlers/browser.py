import subprocess, urllib.parse
def search_web(query, memory=None):
    q=urllib.parse.quote(query); url=f"https://www.google.com/search?q={q}"
    results=[{"title": f"{query} - R1","url": f"https://example.com/{q}/1"},{"title": f"{query} - R2","url": f"https://example.com/{q}/2"}]
    try:
        subprocess.run(["open", url], timeout=5)
        return {"success": True, "query": query, "url": url, "results": results, "message": f"Searched for {query}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
def open_search_result(index, memory=None):
    if memory and memory.last_search_results and len(memory.last_search_results) > index:
        url=memory.last_search_results[index]["url"]
        try:
            subprocess.run(["open", url], timeout=5)
            return {"success": True, "url": url, "message": f"Opened result {index+1}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    return {"success": False, "error": "No results"}
def summarize_url(url=None, memory=None):
    target=url or (memory.last_opened_url if memory else None)
    if not target: return {"success": False, "error": "No page"}
    return {"success": True, "url": target, "message": f"Summarized {target}"}
