"""Entry for the floating orb UI"""
import sys
from PySide6.QtWidgets import QApplication
from assistant.ui.main_window import MainWindow
from assistant.ui.events import EventBus
from assistant.ui.bridge import build_default

def main():
    app = QApplication(sys.argv)
    bus = EventBus()
    bridge_data = build_default(bus)
    
    # Handle both old dict return and new object return
    if isinstance(bridge_data, dict):
        handle_text = bridge_data.get("handle_text")
        # create wrapper object with stop method for aboutToQuit
        class BridgeWrapper:
            def __init__(self, handle):
                self.handle_text = handle
                self.handle = handle
            def stop(self):
                print("[Bridge] stop called")
            def __getitem__(self, key):
                if key == "handle_text":
                    return self.handle_text
                return None
        bridge = BridgeWrapper(handle_text)
        # Store original handle for MainWindow
        window = MainWindow(bus=bus, handle_text=handle_text)
    else:
        bridge = bridge_data
        window = MainWindow(bus=bus, handle_text=getattr(bridge, 'handle_text', None) or getattr(bridge, 'handle', None))

    try:
        app.aboutToQuit.connect(bridge.stop)
    except Exception as e:
        print(f"[WARN] Could not connect stop: {e}")
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
