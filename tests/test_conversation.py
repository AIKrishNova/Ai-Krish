from assistant.intents.router import route
from assistant.conversation.memory import ConversationMemory
def test_greet(): assert route("Hey Krish").name=="greet"
def test_open_app_and_search():
    intent=route("open safari and search for fruits")
    assert intent.name=="open_app_and_search"
    assert intent.slots["query"]=="fruits"
def test_follow_up():
    mem=ConversationMemory(); mem.last_search_results=[{"url":"a"},{"url":"b"}]
    intent=route("Open the second result", mem)
    assert intent.name=="open_search_result"
    assert intent.slots["index"]==1
def test_reference_it():
    mem=ConversationMemory(); mem.last_opened_url="https://example.com/fruits"
    intent=route("Summarize it", mem)
    assert intent.name=="summarize"
def test_correction():
    mem=ConversationMemory(); mem.add("user","Search for fruits",None,None)
    intent=route("No, I meant tropical fruits", mem)
    assert intent.slots["query"]=="tropical fruits"
def test_stop(): assert route("Stop").name=="stop"
