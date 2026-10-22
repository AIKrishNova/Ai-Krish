import unittest

from assistant import config


class AliasTests(unittest.TestCase):
    def test_every_alias_points_to_an_approved_name(self):
        approved = set(config.APPS) | set(config.SITES) | set(config.FOLDERS)
        for alias, target in config.ALIASES.items():
            self.assertIn(target, approved, alias)

    def test_notes_resolves_to_apple_notes(self):
        self.assertEqual(config.ALIASES["notes"], "apple notes")
        self.assertEqual(config.APPS["apple notes"]["mac"], "Notes")

    def test_new_apps_are_approved_on_mac(self):
        for name in ("messages", "reminders", "calendar", "mail"):
            self.assertIn("mac", config.APPS[name])

    def test_unknown_name_is_not_an_alias(self):
        self.assertNotIn("secret thing", config.ALIASES)
        self.assertNotIn("secret thing", config.APPS)


if __name__ == "__main__":
    unittest.main()
