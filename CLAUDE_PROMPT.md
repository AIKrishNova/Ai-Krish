# AI Krish — Project Context & Handoff Prompt

## Project Overview
- **Project**: AI-Krish ([GitHub Repository](https://github.com/AIKrishNova/Ai-Krish))
- **Primary Work Branch**: `siri-full-v1` (active) / `assistant-v1` (stable base)
- **Local Path**: `~/Desktop/Ai-Krish`
- **Python Virtualenv**: `~/.ai-krish/venv/bin/python`

---

## 1. UI Transformation: Legacy vs Native macOS Siri Orb

### Before (Legacy):
- Single file `assistant/ui.py` (now archived as `assistant/legacy_ui.py`)
- Rigid 800x600 grey Tk/Qt window with rectangular buttons, raw terminal output, and static orb images
- Window artifacts: white corner borders, opaque rectangular window chrome, black background bars
- Missing entrypoint `assistant.ui.__main__`

### Now (Native macOS Siri Orb):
- **Glass Card**: Floating 360x410 frameless tool window (`Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool`) with 32px border radius, frosted glass gradient (`rgba(26,26,34,0.72)` with `rgba(255,255,255,0.14)` border)
- **Transparency Rules**: `setAttribute(Qt.WA_TranslucentBackground, True)` and `setAttribute(Qt.WA_NoSystemBackground, True)`
- **Luminous Orb**: Custom 60fps QWidget painter (`OrbWidget`) featuring multi-layer bloom, radial cyan-to-purple gradients, breathing animation during IDLE, reactive audio-level ring expansion during LISTENING, orbital particle effects during THINKING, and audio waveform during SPEAKING
- **Status Pill**: Frosted glass status indicator pill with smooth state transitions (`Ready`, `Listening…`, `Thinking…`, `Speaking…`, `Something went wrong`)
- **Concise Captions**: Real-time feedback label displaying clean, Apple-style status updates (`"Opened Safari"`, `"Searching for '...'"`), automatically truncating multi-line text
- **Circular Action Controls**: 42x36 circular buttons (◉ Listen, ■ Stop, ✕ Cancel) with sleek hover states that automatically minimize in idle state
- **Screen Positioning & Dragging**: Automatically anchors to the top-right corner of the primary macOS display upon waking; can be dragged anywhere on the screen by clicking and moving the card
- **Smooth Opacity Transitions**: 280ms fade-in on wake (`QPropertyAnimation`), auto-dismiss fade-out after 2.6s upon command completion

---

## 2. Global Hotkey & Voice Activation
- **Option+Space Hotkey**: Global hotkey listener powered by `pynput.keyboard.GlobalHotKeys` running on a background daemon thread, safely emitting `bus.wake_detected` to wake the UI on the Qt main loop
- **Wake Word Detection**: Integrated `openwakeword` with ONNX models (`hey_jarvis` model as current stand-in for "Hey Krish"), automatically streaming mic audio via `sounddevice` at 16kHz
- **Speech Recognition**: Local, high-speed transcription powered by `faster-whisper` (`tiny` model on CPU int8)
- **Speech Output**: Low-latency macOS system speech (`say` command via `assistant/audio/tts.py`)

---

## 3. Architecture & File Structure

```
assistant/
├── audio/
│   ├── listener.py        # Sounddevice InputStream, openwakeword, typing loop fallback
│   ├── transcriber.py     # Faster-Whisper tiny CPU transcription
│   └── tts.py             # macOS 'say' command wrapper
├── conversation/
│   └── memory.py          # Multi-turn conversation history & search result context
├── handlers/
│   ├── apps.py            # App opening (Safari, Chrome, Notes, VSCode, Spotify, etc.)
│   ├── browser.py         # Google search, result opening, and URL summarization
│   └── conversation.py    # Conversational greetings, casual talk, stops, fallbacks
├── intents/
│   └── router.py          # Fast deterministic regex routing + optional Ollama fallback
├── tasks/
│   └── manager.py         # Background task lifecycle and cancellation
└── ui/
    ├── __init__.py        # Exports SiriWindow
    ├── __main__.py        # python -m assistant.ui entrypoint (supports --demo)
    ├── bridge.py          # Bridges assistant brain, intents, audio, and EventBus
    ├── events.py          # PySide6 EventBus Qt signals (BUS)
    ├── main_window.py     # SiriWindow frosted glass floating widget
    ├── orb_math.py        # Math routines for orb breathing, bloom, waveforms
    ├── orb_widget.py      # Custom 60fps QPainter orb
    └── states.py          # State machine constants (IDLE, WAKE, LISTENING, etc.)

assets/
└── AppIcon.icns           # Native macOS 512x512 multi-resolution application icon

scripts/
└── build_app.sh           # Builds/updates ~/Applications/AI Krish.app bundle
```

---

## 4. Key Developer Commands

### Launching the Assistant
```bash
# Launch native macOS app bundle
open ~/Applications/AI\ Krish.app

# Run UI directly from source
~/.ai-krish/venv/bin/python -m assistant.ui

# Preview orb animation sequence
~/.ai-krish/venv/bin/python -m assistant.ui --demo

# Run terminal fallback
~/.ai-krish/venv/bin/python -m assistant
```

### Running Test Suite
```bash
cd ~/Desktop/Ai-Krish
PYTHONPATH=. ~/.ai-krish/venv/bin/python -m pytest tests/
# Output: 109 passed in ~12s
```

### Building the Native macOS App Bundle
```bash
cd ~/Desktop/Ai-Krish
./scripts/build_app.sh
```

---

## 5. Guidelines for Future AI / Claude Sessions
1. **Preserve Glass Transparency**: Never remove `Qt.WA_TranslucentBackground` or `Qt.WA_NoSystemBackground`, as this will cause black or white rectangular window artifacts on macOS.
2. **Keep Status Text Consistent**: Status pill text strictly adheres to: `Ready`, `Waking…`, `Listening…`, `Thinking…`, `Speaking…`, `Something went wrong`.
3. **Concise Captions**: Any new intent handler in `assistant/handlers/` should return both `"message"` (for TTS voice) and a concise `"caption"` (for the UI pill, e.g. `"Opened Spotify"`).
4. **Thread-Safe Qt Signals**: Audio and hotkey threads must communicate with the UI strictly by emitting signals through `EventBus` (`bus.wake_detected.emit()`, etc.).
