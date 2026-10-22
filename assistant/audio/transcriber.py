
try:
    from faster_whisper import WhisperModel
    HAS_FASTER = True
except:
    HAS_FASTER = False

class Transcriber:
    def __init__(self):
        self.model = None
        if HAS_FASTER:
            try:
                self.model = WhisperModel("tiny", device="cpu", compute_type="int8")
                print("[Transcriber] tiny model loaded")
            except Exception as e:
                print(f"[Transcriber] failed: {e}")

    def transcribe_file(self, path):
        if not self.model:
            return ""
        segments, _ = self.model.transcribe(path)
        return " ".join([s.text for s in segments]).strip()

    def transcribe(self, path):
        return self.transcribe_file(path)
