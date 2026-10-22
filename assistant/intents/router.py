import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class Intent:
    name: str  # greet, casual, open_app, search_web, open_search_result, summarize, create_reminder, timer, stop, help, unsupported
    slots: dict
    confidence: float
    raw: str

def route_deterministic(text: str) -> Optional[Intent]:
    t = text.lower().strip()
    if re.match(r"^(hey krish|what'?s up|how are you|i'?m bored|hey|hi|hello)$", t):
        return Intent("greet", {}, 0.95, text)
    if re.match(r"^(stop|cancel|abort|never mind)$", t):
        return Intent("stop", {}, 0.99, text)
    
    m = re.search(r"open ([a-zA-Z0-9\s]+?) and search for (.+)", t)
    if m:
        return Intent("open_app_and_search", {"app": m.group(1).strip(), "query": m.group(2).strip()}, 0.9, text)
    
    m = re.search(r"^open ([a-zA-Z0-9\s]+)$", t)
    if m:
        app_cand = m.group(1).strip()
        # avoid matching things like "open the first result"
        if not app_cand.startswith("the ") and "result" not in app_cand:
            return Intent("open_app", {"app": app_cand}, 0.9, text)
    
    m = re.search(r"search for (.+)", t)
    if m:
        return Intent("search_web", {"query": m.group(1).strip()}, 0.85, text)
    
    m = re.search(r"open the (first|second|third|1st|2nd|3rd|\d+).*result", t)
    if m:
        word = m.group(1)
        mapping = {"first":0,"1st":0,"second":1,"2nd":1,"third":2,"3rd":2}
        idx = mapping.get(word, 0)
        if word.isdigit(): idx = int(word)-1
        return Intent("open_search_result", {"index": idx}, 0.9, text)
    
    m = re.search(r"summarize( it)?", t)
    if m:
        return Intent("summarize", {}, 0.8, text)
    
    m = re.search(r"remind me to (.+)", t)
    if m:
        return Intent("create_reminder", {"text": m.group(1).strip()}, 0.7, text)
    
    return None

def route_with_llm_fallback(text, memory_context=""):
    # Try deterministic first
    intent = route_deterministic(text)
    if intent and intent.confidence > 0.8:
        return intent
    
    # Optional Ollama fallback — only if installed
    try:
        import requests
        prompt = f"""You are AI Krish intent classifier. Classify user message into one of: greet, casual, open_app, search_web, open_search_result, summarize, create_reminder, timer, stop, help, unsupported.
Context:
{memory_context}
User: {text}
Return JSON: {{"intent":"...","slots":{{}},"confidence":0.0}}
"""
        r = requests.post("http://127.0.0.1:11434/api/generate", json={
            "model": "llama3.2:1b",
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }, timeout=2)
        if r.status_code == 200:
            import json
            data = json.loads(r.json()["response"])
            return Intent(data["intent"], data.get("slots",{}), data.get("confidence",0.6), text)
    except:
        pass
    
    # Fallback
    if len(text.split()) < 4:
        return Intent("casual", {}, 0.5, text)
    return Intent("unsupported", {}, 0.4, text)

def route(text, memory=None):
    ctx = memory.get_context_prompt() if memory else ""
    # Check for correction
    ref = memory.resolve_reference(text) if memory else None
    if ref and ref["type"] == "correction":
        # treat as new search with corrected query
        m = re.search(r"i meant (.+)", text.lower())
        if m:
            return Intent("search_web", {"query": m.group(1).strip(), "correction": True}, 0.9, text)
    if ref and ref["type"] == "search_index":
        return Intent("open_search_result", {"index": ref["index"], "url": ref["url"]}, 0.95, text)
    if ref and ref["type"] == "last_url":
        if "summarize" in text.lower():
            return Intent("summarize", {"url": ref["url"]}, 0.9, text)
    
    return route_with_llm_fallback(text, ctx)
