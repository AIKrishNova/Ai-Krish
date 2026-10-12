import json, queue, re, subprocess, threading, time, urllib.request, urllib.error
from collections import deque
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

API = "http://127.0.0.1:8000/api/chat/stream"
SR, BLOCK = 16000, 1600
STREAM = sd.InputStream(samplerate=SR, channels=1, dtype="float32", blocksize=BLOCK)
STREAM.start()
STYLE = ("You are NEXUS AI, a personal voice assistant. If asked your name or who you are, say you are Nexus AI. Answer for speech: at most 3 short sentences, plain words, "
         "no markdown, no lists.\n\nQuestion: ")

speech_q = queue.Queue()
current = {"proc": None}

def speaker():
    while True:
        text = speech_q.get()
        if text is None:
            break
        p = subprocess.Popen(["say", "-r", "185", text])
        current["proc"] = p
        p.wait()
        speech_q.task_done()

threading.Thread(target=speaker, daemon=True).start()

def clean(t):
    t = re.sub(r"https?://\S+", "", t)
    return re.sub(r"[*#`_>]", "", t).strip()

def say(t):
    t = clean(t)
    if t:
        speech_q.put(t)

def stop_speaking():
    while not speech_q.empty():
        try:
            speech_q.get_nowait()
            speech_q.task_done()
        except queue.Empty:
            break
    p = current["proc"]
    if p and p.poll() is None:
        p.terminate()

def record():
    subprocess.run(["afplay", "/System/Library/Sounds/Ping.aiff"])
    print("Listening...")
    pre = deque(maxlen=4)
    frames, started, silent, calib = [], False, 0, []
    s = STREAM
    time.sleep(0.3)
    if s.read_available: s.read(s.read_available)
    thr, t0 = 0.008, time.time()
    while True:
        data, _ = s.read(BLOCK)
        level = float(np.sqrt(np.mean(data ** 2)))
        if level > thr:
            if not started:
                frames.extend(pre)
            started, silent = True, 0
            frames.append(data)
        elif started:
            frames.append(data)
            silent += 1
            if silent >= 10:
                break
        else:
            pre.append(data)
            if time.time() - t0 > 8:
                return None
        if time.time() - t0 > 25:
            break
    if not frames:
        return None
    a = np.concatenate(frames).flatten()
    peak = float(np.max(np.abs(a)))
    return a * (0.7 / peak) if peak > 0 else a

def sse(resp):
    event, data = "message", []
    for raw in resp:
        line = raw.decode("utf-8").rstrip("\r\n")
        if line == "":
            if data:
                yield event, "\n".join(data)
            event, data = "message", []
        elif line.startswith("event:"):
            event = line[6:].strip()
        elif line.startswith("data:"):
            data.append(line[5:].lstrip(" "))

def pick(d):
    if isinstance(d, str):
        return d
    if isinstance(d, dict):
        for k in ("text", "content", "delta", "token"):
            if isinstance(d.get(k), str):
                return d[k]
    return ""

def ask(question):
    body = json.dumps({"message": STYLE + question, "max_tokens": 300}).encode()
    req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
    t0, first, buf, full = time.time(), None, "", ""
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            for event, data in sse(resp):
                try:
                    d = json.loads(data)
                except ValueError:
                    d = data
                if event == "token":
                    piece = pick(d)
                    buf += piece
                    full += piece
                    while True:
                        m = re.match(r"(.+?[.!?])\s", buf, re.S)
                        if not m:
                            break
                        if first is None:
                            first = time.time() - t0
                        say(m.group(1))
                        buf = buf[m.end():]
                elif event == "error":
                    msg = (d.get("message") if isinstance(d, dict) else str(d)) or "Something went wrong."
                    print("Error:", msg)
                    say(msg)
                    return
        if buf.strip():
            if first is None:
                first = time.time() - t0
            say(buf)
        print("NEXUS AI:", full.strip())
        if first is not None:
            print(f"(first words after {first:.1f}s)")
    except urllib.error.URLError:
        msg = "I can't reach the backend. Is the server running?"
        print(msg)
        say(msg)

print("Loading speech model...")
model = WhisperModel("base.en", device="cpu", compute_type="int8")
say("Nexus AI online. How can I help?")
print("Ready. Press Enter, then speak. Say 'goodbye' or press Ctrl+C to quit.\n")

try:
    while True:
        input("Press Enter to talk > ")
        stop_speaking()
        audio = record()
        if audio is None:
            print("I didn't hear anything.\n")
            continue
        segs, _ = model.transcribe(audio, language="en", beam_size=1, vad_filter=True)
        text = " ".join(s.text.strip() for s in segs).strip()
        if not text:
            print("I didn't catch that.\n")
            continue
        print("You:", text)
        if text.lower().strip(" .!") in ("goodbye", "exit", "quit"):
            say("Goodbye.")
            speech_q.join()
            break
        ask(text)
        speech_q.join()
        print()
except KeyboardInterrupt:
    stop_speaking()
    print("\nBye.")
