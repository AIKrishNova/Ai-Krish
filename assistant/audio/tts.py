
import subprocess
class TTS:
    def speak(self, text):
        print(f"[TTS] {text}")
        try:
            subprocess.run(["say", text[:180]], check=False)
        except:
            pass
