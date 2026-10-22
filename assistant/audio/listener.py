
import threading
import time

class MicListener:
    def __init__(self, transcriber, tts, bridge, bus):
        self.transcriber = transcriber
        self.tts = tts
        self.bridge = bridge
        self.bus = bus
        self.running = False

    def start(self):
        if self.running:
            return
        self.running = True
        print("[Listener] Starting - type to talk to orb (enter text)")
        def loop():
            while self.running:
                try:
                    txt = input("You: ")
                    if not txt:
                        continue
                    if txt.lower() in ("exit","quit","stop"):
                        self.bridge.handle_text("stop")
                        continue
                    result = self.bridge.handle_text(txt)
                    self.tts.speak(result.get("message",""))
                except EOFError:
                    break
                except Exception as e:
                    print(f"[Listener error] {e}")
                    time.sleep(0.5)
        threading.Thread(target=loop, daemon=True).start()

    def stop(self):
        self.running = False
        print("[Listener] Stopped")
