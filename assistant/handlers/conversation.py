def handle_greet(text, memory=None):
    return {"success": True, "message": "Hey! How can I help you?", "caption": "Hey Krish!", "type": "conversation"}

def handle_casual(text, memory=None):
    return {"success": True, "message": "Ready when you are.", "caption": "Ready to help", "type": "conversation"}

def handle_stop(text, memory=None):
    return {"success": True, "message": "Stopped.", "caption": "Stopped", "type": "stop", "cancelled": True}

def handle_unsupported(text, memory=None):
    clean = text[:30] if text else "that"
    return {"success": False, "message": f"I can't do '{clean}' yet - try opening apps or searching the web", "caption": "Not supported yet", "type": "unsupported"}
