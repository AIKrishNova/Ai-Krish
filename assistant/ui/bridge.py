from ..conversation.memory import ConversationMemory
from ..intents.router import route
from ..handlers.apps import open_app, open_app_and_search
from ..handlers import browser as browser_handler
from ..handlers import conversation as conv_handler
from ..tasks.manager import TaskManager

class Bridge:
    def __init__(self, bus):
        self.bus = bus
        self.memory = ConversationMemory()
        self.task_mgr = TaskManager()

    def handle_text(self, text: str):
        if not text or not text.strip():
            return {"success": False, "message": "Empty"}
        intent = route(text, self.memory)
        print(f"[Krish] Intent: {intent.name} {intent.slots}")
        try: self.bus.listening_started.emit()
        except: pass
        try: self.bus.processing_started.emit()
        except: pass

        if intent.name == "stop":
            self.task_mgr.cancel()
            result = conv_handler.handle_stop(text, self.memory)
            try: self.bus.task_cancelled.emit()
            except: pass
        elif intent.name == "greet":
            result = conv_handler.handle_greet(text, self.memory)
        elif intent.name in ("casual", "unsupported"):
            result = conv_handler.handle_casual(text, self.memory) if intent.name=="casual" else conv_handler.handle_unsupported(text, self.memory)
        elif intent.name == "open_app":
            result = open_app(intent.slots.get("app",""))
        elif intent.name == "open_app_and_search":
            result = open_app_and_search(intent.slots.get("app","safari"), intent.slots.get("query",""))
        elif intent.name == "search_web":
            result = browser_handler.search_web(intent.slots.get("query",""), self.memory)
        elif intent.name == "open_search_result":
            result = browser_handler.open_search_result(intent.slots.get("index",0), self.memory)
        elif intent.name == "summarize":
            result = browser_handler.summarize_url(intent.slots.get("url"), self.memory)
        else:
            result = conv_handler.handle_unsupported(text, self.memory)

        self.memory.add("user", text, intent.name, None)
        self.memory.add("assistant", result.get("message",""), intent.name, result)

        msg = result.get("message","")[:90]
        try:
            if result.get("success"):
                self.bus.caption_changed.emit(msg)
                self.bus.speaking_started.emit()
                self.bus.speaking_finished.emit()
                self.bus.task_completed.emit()
            else:
                self.bus.caption_changed.emit(msg)
                self.bus.task_failed.emit(msg)
        except Exception as e:
            print(f"[BUS emit fail] {e}")
        
        print(f"[Krish] -> {result['message']}")
        return result

    def listen_and_handle(self, text=None):
        if text:
            return self.handle_text(text)
        print("[Bridge] listen_and_handle called without text")
        return self.handle_text("hello")

    def start_listening(self):
        return self.listen_and_handle()

    def stop(self):
        print("[Bridge] stop called")
        self.task_mgr.cancel()
        try: self.bus.task_cancelled.emit()
        except: pass

def build_default(bus=None):
    from .events import EventBus
    if bus is None:
        bus = EventBus()
    return Bridge(bus)
