import unittest

from assistant.commands import HELP


class HelpTextTests(unittest.TestCase):
    def test_lists_reminders(self):
        self.assertIn("remind me in 10 minutes", HELP)
        self.assertIn("cancel all reminders", HELP)

    def test_no_stray_quote_or_escape_characters(self):
        self.assertNotIn('\\n"', HELP)
        self.assertNotIn('"  remind', HELP)


if __name__ == "__main__":
    unittest.main()
