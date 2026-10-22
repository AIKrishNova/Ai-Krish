import unittest

from assistant.commands import Reply
from assistant.ui_logic import run_command


class FakeSpeaker:
    def __init__(self):
        self.enabled = True
        self.spoken = []

    def supported(self):
        return True

    def speak(self, text):
        self.spoken.append(text)

    def stop(self):
        pass


class FakeRouter:
    def __init__(self):
        self.pending = "delete 3"

    def handle(self, line):
        return Reply("router: " + line, quit=(line == "exit"))


class FakeReminders:
    def list_text(self):
        return "You have no active reminders or timers."


class RunCommandTests(unittest.TestCase):
    def setUp(self):
        self.speaker, self.router, self.rem = FakeSpeaker(), FakeRouter(), FakeReminders()

    def test_normal_command_goes_to_router_and_is_spoken(self):
        text, quit_ = run_command("open safari", self.router, self.speaker, self.rem)
        self.assertEqual(text, "router: open safari")
        self.assertFalse(quit_)
        self.assertEqual(self.speaker.spoken, ["router: open safari"])

    def test_exit_quits_without_speaking(self):
        text, quit_ = run_command("exit", self.router, self.speaker, self.rem)
        self.assertTrue(quit_)
        self.assertEqual(self.speaker.spoken, [])

    def test_speak_off_cancels_pending_delete(self):
        text, quit_ = run_command("speak off", self.router, self.speaker, self.rem)
        self.assertEqual(text, "Spoken replies are off.")
        self.assertIsNone(self.router.pending)
        self.assertFalse(self.speaker.enabled)

    def test_reminder_command_is_handled(self):
        text, _ = run_command("list reminders", self.router, self.speaker, self.rem)
        self.assertIn("no active reminders", text)


if __name__ == "__main__":
    unittest.main()
