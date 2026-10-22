import random
def handle_greet(text, memory=None):
    return {"success": True, "message": "Hey! I am here.", "type":"conversation"}
def handle_casual(text, memory=None):
    return {"success": True, "message": "Nothing much! Just hanging out, ready to help.", "type":"conversation"}
def handle_stop(text, memory=None):
    return {"success": True, "message":"Stopped.", "type":"stop","cancelled":True}
def handle_unsupported(text, memory=None):
    return {"success": False, "message": f"I cant do '{text}' yet - try open apps or search web", "type":"unsupported"}
