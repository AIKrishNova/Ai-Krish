from ..conversation.memory import ConversationMemory
from ..intents.router import route
from ..handlers import apps as apps_handler, browser as browser_handler, conversation as conv_handler
from ..tasks.manager import TaskManager
from .events import BUS

memory = ConversationMemory()
task_mgr = TaskManager()

def handle_text(text: str):
    intent = route(text, memory)
    print(f"[Krish] Intent: {intent.name} {intent.slots}")
    BUS.listening_started.emit()

    if intent.name == "stop":
        task_mgr.cancel()
        result = conv_handler.handle_stop(text, memory)
        BUS.task_cancelled.emit()
    elif intent.name == "greet":
        result = conv_handler.handle_greet(text, memory)
    elif intent.name in ("casual", "unsupported"):
        result = conv_handler.handle_casual(text, memory) if intent.name=="casual" else conv_handler.handle_unsupported(text, memory)
    elif intent.name == "open_app":
        result = apps_handler.open_app(intent.slots.get("app",""))
    elif intent.name == "open_app_and_search":
        result = apps_handler.open_app_and_search(intent.slots.get("app","safari"), intent.slots.get("query",""))
    elif intent.name == "search_web":
        result = browser_handler.search_web(intent.slots.get("query",""), memory)
    elif intent.name == "open_search_result":
        result = browser_handler.open_search_result(intent.slots.get("index",0), memory)
    elif intent.name == "summarize":
        result = browser_handler.summarize_url(intent.slots.get("url"), memory)
    else:
        result = conv_handler.handle_unsupported(text, memory)

    memory.add("user", text, intent.name, None)
    memory.add("assistant", result.get("message",""), intent.name, result)

    if result.get("success"):
        BUS.speaking_started.emit(result["message"][:70])
        BUS.task_completed.emit(result["message"][:70])
    else:
        BUS.task_failed.emit(result.get("message","Failed")[:90])
    
    print(f"[Krish] -> {result['message']}")
    return result
