"""Reminders and timers: understanding what you typed or said.

(The class that does the counting down is added in the next step.)
"""
import re

from assistant.commands import WAKE

MAX_SECONDS = 24 * 60 * 60  # 24 hours
_UNIT_SECONDS = {"h": 3600, "m": 60, "s": 1}
_PAIR = re.compile(
    r"(\d+)\s*(hours?|hrs?|h|minutes?|mins?|m|seconds?|secs?|s)\b", re.IGNORECASE
)
_REMIND_IN = re.compile(
    r"remind me in (?P<dur>.+?)\s*(?:,|:|\bto\b|\bthat\b|\babout\b)\s*(?P<what>.+)",
    re.IGNORECASE,
)
_REMIND_TO = re.compile(r"remind me to (?P<what>.+?)\s+in (?P<dur>\d.*)", re.IGNORECASE)
_TIMER = re.compile(
    r"(?:(?:set|start)\s+(?:a\s+)?)?timer\s+(?:for\s+)?(?P<dur>\d.*)", re.IGNORECASE
)
_LIST = re.compile(r"(?:list|show)\s+(?:my\s+)?(?:reminders|timers)", re.IGNORECASE)
_CANCEL = re.compile(
    r"(?:cancel|delete|remove)\s+(?:reminder|timer)\s+#?(?P<id>\d+)", re.IGNORECASE
)
_CANCEL_ALL = re.compile(
    r"(?:cancel|delete|remove|clear)\s+(?:all\s+)?(?:my\s+)?(?:reminders|timers)",
    re.IGNORECASE,
)


def parse_duration(text):
    """'1 hour 30 minutes' -> 5400. Returns None if it is not a clear time."""
    pairs = _PAIR.findall(text or "")
    if not pairs:
        return None
    leftover = re.sub(r"\b(?:and|an|a)\b|[,\s]", "", _PAIR.sub("", text), flags=re.I)
    if leftover:
        return None
    total = sum(int(n) * _UNIT_SECONDS[u[0].lower()] for n, u in pairs)
    return total or None


def format_duration(seconds):
    seconds = int(round(seconds))
    parts = []
    for name, size in (("hour", 3600), ("minute", 60), ("second", 1)):
        count, seconds = divmod(seconds, size)
        if count:
            parts.append("%d %s%s" % (count, name, "" if count == 1 else "s"))
    return " ".join(parts) or "0 seconds"


def _plain(raw):
    return WAKE.sub("", (raw or "").strip(), count=1).strip().rstrip(".!?").strip()


def _timed(kind, duration_text, what):
    seconds = parse_duration(duration_text)
    if seconds is None:
        return ("error", "I could not understand that time. Try: remind me in 10 minutes to stretch")
    if seconds > MAX_SECONDS:
        return ("error", "That is longer than 24 hours. Reminders only last while I am running, so please pick a shorter time.")
    return (kind, seconds, what)


def parse_reminder_command(raw):
    """None if this is not a reminder or timer command, otherwise a tuple."""
    text = _plain(raw)
    if _LIST.fullmatch(text):
        return ("list",)
    if _CANCEL_ALL.fullmatch(text):
        return ("cancel_all",)
    m = _CANCEL.fullmatch(text)
    if m:
        return ("cancel", int(m.group("id")))
    m = _TIMER.fullmatch(text)
    if m:
        return _timed("timer", m.group("dur"), "")
    m = _REMIND_IN.fullmatch(text) or _REMIND_TO.fullmatch(text)
    if m:
        return _timed("remind", m.group("dur"), m.group("what").strip())
    return None


import threading
import time


class Reminders:
    """Keeps reminders and timers while the assistant is running.

    They are NOT saved: closing the assistant forgets them.
    """

    def __init__(self, notify, timer_factory=None, clock=None, max_active=20):
        self._notify = notify
        self._make_timer = timer_factory or threading.Timer
        self._clock = clock or time.time
        self._max = max_active
        self._items = {}
        self._next_id = 1
        self._lock = threading.Lock()

    def add(self, kind, seconds, what):
        with self._lock:
            if len(self._items) >= self._max:
                return "You already have %d active. Cancel one first." % self._max
            number = self._next_id
            self._next_id += 1
            timer = self._make_timer(seconds, self._fire, args=(number,))
            timer.daemon = True
            self._items[number] = {
                "kind": kind,
                "what": what,
                "due": self._clock() + seconds,
                "timer": timer,
            }
            timer.start()
        wait = format_duration(seconds)
        if kind == "timer":
            return "Timer #%d set for %s. (Only while I am running.)" % (number, wait)
        return "Reminder #%d set for %s from now: %s (Only while I am running.)" % (number, wait, what)

    def _fire(self, number):
        with self._lock:
            item = self._items.pop(number, None)
        if item is None:
            return
        if item["kind"] == "timer":
            self._notify("Timer #%d is done." % number)
        else:
            self._notify("Reminder: %s" % item["what"])

    def list_text(self):
        with self._lock:
            items = sorted(self._items.items(), key=lambda pair: pair[1]["due"])
            now = self._clock()
        if not items:
            return "You have no active reminders or timers."
        lines = ["Active reminders and timers:"]
        for number, item in items:
            left = format_duration(max(0, item["due"] - now))
            label = "timer" if item["kind"] == "timer" else "remind: " + item["what"]
            lines.append("#%d  in %s  (%s)" % (number, left, label))
        return "\n".join(lines)

    def cancel(self, number):
        with self._lock:
            item = self._items.pop(number, None)
        if item is None:
            return "I have no reminder or timer #%d." % number
        item["timer"].cancel()
        return "Cancelled #%d." % number

    def cancel_all(self):
        with self._lock:
            items = list(self._items.values())
            self._items.clear()
        for item in items:
            item["timer"].cancel()
        return "Cancelled %d." % len(items) if items else "You have nothing to cancel."

    def stop(self):
        self.cancel_all()


def handle_reminder_command(raw, reminders):
    """Returns the reply text, or None if this is not a reminder/timer command."""
    parsed = parse_reminder_command(raw)
    if parsed is None:
        return None
    kind = parsed[0]
    if kind == "error":
        return parsed[1]
    if kind == "list":
        return reminders.list_text()
    if kind == "cancel_all":
        return reminders.cancel_all()
    if kind == "cancel":
        return reminders.cancel(parsed[1])
    return reminders.add(kind, parsed[1], parsed[2])
