"""Small, safe probe for the NVIDIA API. Never prints the API key."""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

BASE_URL = "https://integrate.api.nvidia.com/v1"
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
KEY = ""


def safe(text):
    """Remove the API key from any text before printing."""
    return str(text).replace(KEY, "[KEY]") if KEY else str(text)


def load_key():
    global KEY
    load_dotenv(ENV_PATH)
    KEY = os.getenv("NVIDIA_API_KEY", "").strip()
    if not KEY:
        sys.exit("NVIDIA_API_KEY was not found in " + str(ENV_PATH))
    print("key loaded: yes | starts with nvapi-:", KEY.startswith("nvapi-"))
    return {"Authorization": "Bearer " + KEY, "Content-Type": "application/json"}


def show_text(label, value):
    if value is None or value == "":
        print(f"  {label}: (empty)")
    else:
        text = str(value).replace("\n", " ")
        print(f"  {label}: {text[:300]}" + ("..." if len(text) > 300 else ""))


def request_id(r):
    return r.headers.get("nvcf-reqid") or r.headers.get("x-request-id") or "(none)"


def cmd_check(args):
    headers = load_key()
    t0 = time.perf_counter()
    r = httpx.get(BASE_URL + "/models", headers=headers, timeout=20.0)
    print(f"GET /models -> HTTP {r.status_code} in {time.perf_counter() - t0:.2f}s")
    ids = sorted(m.get("id", "") for m in r.json().get("data", []))
    print("models listed:", len(ids))
    words = [w.lower() for w in args.filter]
    for model_id in ids:
        if any(w in model_id.lower() for w in words):
            print("   ", model_id)


def run_plain(url, headers, body, timeout, t0):
    r = httpx.post(url, headers=headers, json=body, timeout=timeout)
    print(f"HTTP {r.status_code} after {time.perf_counter() - t0:.1f}s")
    print("  request id:", request_id(r))
    if r.status_code != 200:
        print("  error body:", safe(r.text[:500]))
        return
    data = r.json()
    choice = data["choices"][0]
    msg = choice.get("message") or {}
    print("  finish_reason:", choice.get("finish_reason"))
    print("  message fields:", sorted(msg.keys()))
    show_text("content", msg.get("content"))
    show_text("reasoning", msg.get("reasoning_content") or msg.get("reasoning"))
    print("  usage:", data.get("usage"))


def run_stream(url, headers, body, timeout, t0):
    content, reasoning, fields = [], [], set()
    first_any = first_content = finish = usage = None
    chunks = 0
    with httpx.stream("POST", url, headers=headers, json=body, timeout=timeout) as r:
        print(f"HTTP {r.status_code} (headers) after {time.perf_counter() - t0:.1f}s")
        print("  request id:", request_id(r))
        if r.status_code != 200:
            r.read()
            print("  error body:", safe(r.text[:500]))
            return
        for line in r.iter_lines():
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]":
                break
            try:
                obj = json.loads(payload)
            except json.JSONDecodeError:
                continue
            chunks += 1
            if first_any is None:
                first_any = time.perf_counter() - t0
            usage = obj.get("usage") or usage
            for choice in obj.get("choices") or []:
                delta = choice.get("delta") or {}
                fields.update(k for k, v in delta.items() if v not in (None, ""))
                if delta.get("content"):
                    if first_content is None:
                        first_content = time.perf_counter() - t0
                    content.append(delta["content"])
                piece = delta.get("reasoning_content") or delta.get("reasoning")
                if piece:
                    reasoning.append(piece)
                finish = choice.get("finish_reason") or finish
    print(f"  chunks: {chunks} | first chunk: {first_any} | first answer text: {first_content}")
    print("  delta fields that carried data:", sorted(fields))
    print("  finish_reason:", finish)
    show_text("content", "".join(content))
    show_text("reasoning", "".join(reasoning))
    print("  usage:", usage)
    print(f"  total time: {time.perf_counter() - t0:.1f}s")


def cmd_chat(args):
    headers = load_key()
    body = {
        "model": args.model,
        "messages": [{"role": "user", "content": args.prompt}],
        "max_tokens": args.max_tokens,
        "temperature": 0.2,
        "stream": args.stream,
    }
    if args.effort:
        body["reasoning_effort"] = args.effort
    if args.extra:
        body.update(json.loads(args.extra))
    print("request body (no secrets):", json.dumps(body))
    timeout = httpx.Timeout(connect=10.0, read=args.timeout, write=10.0, pool=10.0)
    url = BASE_URL + "/chat/completions"
    t0 = time.perf_counter()
    try:
        if args.stream:
            run_stream(url, headers, body, timeout, t0)
        else:
            run_plain(url, headers, body, timeout, t0)
    except httpx.TimeoutException as e:
        print(f"RESULT: {type(e).__name__} after {time.perf_counter() - t0:.1f}s")
    except httpx.HTTPError as e:
        print(f"RESULT: {type(e).__name__} after {time.perf_counter() - t0:.1f}s: {safe(e)}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="load key and list model IDs")
    c.add_argument("--filter", nargs="+", default=["glm", "deepseek", "llama-3.1-8b"])
    c.set_defaults(func=cmd_check)
    m = sub.add_parser("chat", help="send one chat request")
    m.add_argument("model")
    m.add_argument("--prompt", default="Reply with exactly: NEXUS is online")
    m.add_argument("--max-tokens", type=int, default=30)
    m.add_argument("--timeout", type=float, default=30.0)
    m.add_argument("--stream", action="store_true")
    m.add_argument("--effort", choices=["low", "high", "max"])
    m.add_argument("--extra", help="extra JSON merged into the request body")
    m.set_defaults(func=cmd_chat)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
