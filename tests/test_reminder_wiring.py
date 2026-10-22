import unittest

from assistant.__main__ import make_notifier, process
from assistant.reminders import Reminders


class FakeTimer:
    def __init__(self, seconds, fn, args=()):
        self.seconds, self.fn, self.args = seconds, fn, args
        self.daemon = False
        self.started = False
        self.cancelled = False

    def start(self):
        self.started = True

    def cancel(self):
        self.cancelled = True


class FakeSpeaker:
    enabled = False

    def __init__(self):
        self.spoken = []

    def speak(self, text):
        self.spoken.append(text)

    def stop(self):
        pass

    def supported(self):
        return True


class FakeReply:
    def __init__(self, text):
        self.text = text
        self.quit = False


class FakeRouter:
    def __init__(self):
        self.pending = "delete 3"
        self.lines = []

    def handle(self, line):
        self.lines.append(line)
        return FakeReply("router: " + line)


class ReminderWiringTests(unittest.TestCase):
    def setUp(self):
        self.speaker = FakeSpeaker()
        self.router = FakeRouter()
        self.reminders = Reminders(make_notifier(self.speaker), timer_factory=FakeTimer)

    def test_reminder_command_skips_router_and_clears_pending(self):
        quit_now = process("remind me in 5 minutes to stretch", self.router, self.speaker, self.reminders)
        self.assertFalse(quit_now)
        self.assertEqual(self.router.lines, [])
        self.assertIsNone(self.router.pending)
        self.assertIn("Reminder #1", self.speaker.spoken[0])

    def test_other_commands_still_reach_router(self):
        process("open safari", self.router, self.speaker, self.reminders)
        self.assertEqual(self.router.lines, ["open safari"])
        self.assertEqual(self.router.pending, "delete 3")

    def test_notifier_speaks_when_timer_fires(self):
        process("set a timer for 1 minute", self.router, self.speaker, self.reminders)
        self.reminders._fire(1)
        self.assertEqual(self.speaker.spoken[-1], "Timer #1 is done.")

    def test_stop_cancels_timers(self):
        process("remind me in 5 minutes to stretch", self.router, self.speaker, self.reminders)
        timer = self.reminders._items[1]["timer"]
        self.reminders.stop()
        self.assertTrue(timer.cancelled)


if __name__ == "__main__":
    unittest.main()
