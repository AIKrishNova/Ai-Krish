# NEXUS AI

An open-source personal AI assistant: a FastAPI backend that streams answers from the NVIDIA API, plus a voice assistant that listens, thinks, and speaks.

> Demo video: coming soon

## Features

- FastAPI backend with streaming chat (`/api/chat/stream`)
- Voice assistant: microphone capture, local speech-to-text with faster-whisper (`base.en`), spoken replies
- Secret redaction for logs and error payloads
- Configuration through environment variables only; no keys in the repo

## Requirements

- Python 3.10 or newer
- An NVIDIA API key (from build.nvidia.com)
- For the voice assistant: macOS (it uses `afplay`) and a working microphone

## Quick start: backend

1. `cd backend`
2. Copy `.env.example` to `.env` and add your own NVIDIA API key.
3. Install dependencies and run: `python -m uvicorn app.main:app --port 8000`

## Quick start: voice assistant

Keep the backend running on port 8000, then in a second terminal:

1. `python3 -m venv .venv && source .venv/bin/activate`
2. `pip install -r voice/requirements.txt`
3. `python voice/assistant.py`

The first run downloads the Whisper model. macOS will ask for microphone permission. The microphone stream stays open while the assistant runs, so the orange mic indicator stays on.

Voice detection uses a fixed volume threshold (`thr` in `record()`), tuned for a quiet room. If it never triggers or triggers on background noise, adjust that value.

## Project layout

- `backend/` FastAPI service
- `voice/` voice assistant
- `docs/` documentation

## Contributing

Issues and pull requests are welcome. Never commit `.env` files or API keys.

## License

MIT. See `LICENSE`.
