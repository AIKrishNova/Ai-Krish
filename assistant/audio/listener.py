import threading
import queue
import tempfile
import wave
import numpy as np

try:
    import sounddevice as sd
    HAS_AUDIO = True
except Exception as e:
    HAS_AUDIO = False
    print("[Listener] sounddevice not available:", e)

try:
    from openwakeword.model import Model as WakeModel
    HAS_WAKE = True
except Exception as e:
    HAS_WAKE = False
    print("[Listener] openwakeword not available:", e)


class MicListener:
    def __init__(self, transcriber, tts, bridge, bus=None):
        self.transcriber = transcriber
        self.tts = tts
        self.bridge = bridge
        self.bus = bus
        self.running = False
        self.q = queue.Queue()
        self.rate = 16000
        self.block = 1280
        self.wake_model = None
        if HAS_WAKE and HAS_AUDIO:
            try:
                self.wake_model = WakeModel(wakeword_models=["hey_jarvis"], inference_framework="onnx")
                print("[Listener] wake word ready: say 'hey jarvis' (stand-in for hey Krish)")
            except Exception as e:
                print("[Listener] wake model failed:", e)

    def start(self):
        if self.running:
            return
        self.running = True
        print("[Listener] Type at the You: prompt, or say 'hey jarvis'")
        threading.Thread(target=self._typing_loop, daemon=True).start()
        if self.wake_model is not None:
            threading.Thread(target=self._mic_loop, daemon=True).start()

    def stop(self):
        self.running = False
        print("[Listener] Stopped")

    def _typing_loop(self):
        while self.running:
            try:
                text = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                return
            if text:
                self.bridge.handle_text(text)

    def _mic_loop(self):
        def cb(indata, frames, t, status):
            self.q.put(indata[:, 0].copy())
        try:
            with sd.InputStream(samplerate=self.rate, channels=1, dtype="int16",
                                blocksize=self.block, callback=cb):
                while self.running:
                    chunk = self.q.get()
                    scores = self.wake_model.predict(chunk)
                    if any(v > 0.5 for v in scores.values()):
                        print("[Listener] wake word heard - speak now")
                        self.wake_model.reset()
                        if self.bus:
                            try:
                                self.bus.wake_detected.emit()
                                self.bus.listening_started.emit()
                            except Exception:
                                pass
                        self._record_and_handle()
        except Exception as e:
            print("[Listener] mic error (check Terminal microphone permission):", e)

    def _record_and_handle(self):
        frames = []
        needed = int(5 * self.rate / self.block)
        for _ in range(needed):
            if not self.running:
                return
            chunk = self.q.get()
            frames.append(chunk)
            if self.bus:
                try:
                    lvl = float(np.max(np.abs(chunk))) / 32768.0
                    self.bus.audio_level.emit(min(1.0, lvl * 2.0))
                except Exception:
                    pass
        if self.bus:
            try:
                self.bus.processing_started.emit()
            except Exception:
                pass
        audio = np.concatenate(frames)
        text = self._transcribe(audio)
        print("[Listener] heard:", text)
        if text:
            if self.bus:
                try:
                    self.bus.transcript_updated.emit(text, True)
                except Exception:
                    pass
            self.bridge.handle_text(text)
        else:
            if self.bus:
                try:
                    self.bus.task_failed.emit("I didn't catch that")
                except Exception:
                    pass

    def _transcribe(self, audio):
        for name in ("transcribe_file", "transcribe_array", "transcribe_audio", "transcribe"):
            fn = getattr(self.transcriber, name, None)
            if fn is None:
                continue
            try:
                return fn(audio.astype(np.float32) / 32768.0)
            except Exception:
                pass
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    path = f.name
                with wave.open(path, "wb") as w:
                    w.setnchannels(1)
                    w.setsampwidth(2)
                    w.setframerate(self.rate)
                    w.writeframes(audio.tobytes())
                return fn(path)
            except Exception as e:
                print("[Listener] transcribe failed:", e)
        return ""
