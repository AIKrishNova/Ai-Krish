import unittest

from assistant import commands


class OpenNotesRoutingTests(unittest.TestCase):
    def _first_match(self, text):
        router = commands.Router(store=None, desktop=None)
        for pattern, handler in router._routes:
            if pattern.fullmatch(text):
                return handler.__name__
        return None

    def test_open_notes_goes_to_open_app(self):
        self.assertEqual(self._first_match("open notes"), "_open")

    def test_open_the_notes_app_goes_to_open_app(self):
        self.assertEqual(self._first_match("open the notes app"), "_open")

    def test_list_notes_still_lists(self):
        self.assertEqual(self._first_match("list notes"), "_list")
        self.assertEqual(self._first_match("show my notes"), "_list")
        self.assertEqual(self._first_match("notes"), "_list")

    def test_latest_note_still_reads_store(self):
        self.assertEqual(self._first_match("open my latest note"), "_latest")


if __name__ == "__main__":
    unittest.main()
