import json, os
from collections import deque
from datetime import datetime

MEM_PATH = os.path.expanduser("~/.ai-krish/memory.json")
PREF_PATH = os.path.expanduser("~/.ai-krish/preferences.json")

class ConversationMemory:
    def __init__(self, max_turns=12):
        self.turns = deque(maxlen=max_turns)
        self.last_search_results = []
        self.last_opened_url = None
        self.last_tool = None
        self.preferences = self._load(PREF_PATH)
        
    def _load(self, path):
        if os.path.exists(path):
            try:
                with open(path) as f: return json.load(f)
            except: return {}
        return {}
    
    def _save_prefs(self):
        os.makedirs(os.path.dirname(PREF_PATH), exist_ok=True)
        with open(PREF_PATH, 'w') as f: json.dump(self.preferences, f, indent=2)

    def add(self, role, text, intent=None, tool_result=None):
        self.turns.append({
            "role": role,
            "text": text,
            "intent": intent,
            "time": datetime.now().isoformat(),
            "tool_result": tool_result
        })
        if tool_result:
            self.last_tool = tool_result
            if tool_result.get("results"):
                self.last_search_results = tool_result["results"]
            if tool_result.get("url"):
                self.last_opened_url = tool_result["url"]

    def resolve_reference(self, text):
        t = text.lower()
        # "second result", "first one", "it", "that"
        if any(x in t for x in ["second result", "2nd result"]):
            if len(self.last_search_results) >=2:
                return {"type":"search_index","index":1,"url":self.last_search_results[1].get("url")}
        if any(x in t for x in ["first result","first one","top result"]):
            if self.last_search_results:
                return {"type":"search_index","index":0,"url":self.last_search_results[0].get("url")}
        if "second" in t and "result" not in t and self.last_search_results:
            # generic second
            pass
        if t.strip() in ["it","that","summarize it","open it"]:
            if self.last_opened_url:
                return {"type":"last_url","url":self.last_opened_url}
        if "no, i meant" in t or "i meant" in t:
            return {"type":"correction","original": list(self.turns)[-2] if len(self.turns)>=2 else None}
        return None

    def get_context_prompt(self):
        # last 6 turns for LLM
        ctx = []
        for turn in list(self.turns)[-6:]:
            ctx.append(f"{turn['role']}: {turn['text']}")
        return "\n".join(ctx)
