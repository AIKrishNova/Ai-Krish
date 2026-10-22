import unittest

from assistant import listen


class CommandHintTests(unittest.TestCase):
    def test_hint_mentions_core_commands(self):
        for phrase in ("Open Safari", "Take a note", "Set a timer", "Remind me"):
            self.assertIn(phrase, listen.COMMAND_HINT)

    def test_hint_is_short(self):
        # Whisper only reads a limited prompt, so keep it small.
        self.assertLess(len(listen.COMMAND_HINT), 400)


if __name__ == "__main__":
    unittest.main()
