import unittest

from assistant.listen import (
    Endpointer,
    Listener,
    clean_transcript,
    is_listen_command,
    is_stop_listening_command,
)


def run(endpointer, levels):
    state = Endpointer.CONTINUE
    for level in levels:
        state = endpointer.feed(level)
        if state != Endpointer.CONTINUE:
            break
    return state


class EndpointerTests(unittest.TestCase):
    def test_speech_then_pause_finishes(self):
        ep = Endpointer()
        levels = [0.001] * 5 + [0.1] * 3 + [0.0] * 12
        self.assertEqual(run(ep, levels), Endpointer.DONE)
        self.assertTrue(ep.started)

    def test_short_pause_does_not_finish(self):
        ep = Endpointer()
        levels = [0.001] * 5 + [0.1] * 3 + [0.0] * 5 + [0.1] * 3
        self.assertEqual(run(ep, levels), Endpointer.CONTINUE)

    def test_no_speech_times_out(self):
        ep = Endpointer()
        self.assertEqual(run(ep, [0.001] * 200), Endpointer.NO_SPEECH)
        self.assertFalse(ep.started)

    def test_very_long_speech_is_cut_off(self):
        ep = Endpointer()
        levels = [0.001] * 5 + [0.1] * 300
        self.assertEqual(run(ep, levels), Endpointer.MAX_LENGTH)
        self.assertEqual(ep.blocks, 150)

    def test_threshold_is_capped(self):
        ep = Endpointer()
        run(ep, [0.02] * 5)
        self.assertEqual(ep.threshold, 0.05)

    def test_threshold_has_a_floor(self):
        ep = Endpointer()
        run(ep, [0.0] * 5)
        self.assertEqual(ep.threshold, 0.01)


class CleanTranscriptTests(unittest.TestCase):
    def test_spaces_are_tidied(self):
        self.assertEqual(clean_transcript("  Hello   there "), "Hello there")

    def test_blank_audio_tag_removed(self):
        self.assertEqual(clean_transcript("[BLANK_AUDIO]"), "")

    def test_sound_tags_removed_but_words_kept(self):
        self.assertEqual(clean_transcript("(music) take a note"), "take a note")

    def test_silence_ghosts_and_punctuation_removed(self):
        self.assertEqual(clean_transcript("Thank you."), "")
        self.assertEqual(clean_transcript("."), "")
        self.assertEqual(clean_transcript(None), "")

    def test_normal_command_unchanged(self):
        self.assertEqual(clean_transcript("take a note: buy milk"), "take a note: buy milk")


class CommandDetectionTests(unittest.TestCase):
    def test_listen_commands(self):
        for text in ("listen", "Listen.", "Hey Krish, listen", "start listening"):
            self.assertTrue(is_listen_command(text), text)

    def test_not_listen_commands(self):
        for text in ("listen to music", "take a note: listen", "stop listening"):
            self.assertFalse(is_listen_command(text), text)

    def test_stop_listening(self):
        self.assertTrue(is_stop_listening_command("stop listening"))
        self.assertTrue(is_stop_listening_command("Hey Krish, stop listening!"))
        self.assertFalse(is_stop_listening_command("stop speaking"))


class ListenerTests(unittest.TestCase):
    def test_missing_libraries_are_reported_without_touching_the_microphone(self):
        def broken(name):
            raise ImportError(name)

        shown = []
        listener = Listener(importer=broken)
        ok, why = listener.check_libraries()
        self.assertFalse(ok)
        self.assertIn("venv", why)
        result = listener.listen_once(shown.append)
        self.assertIsNone(result.text)
        self.assertIn("venv", result.error)
        self.assertEqual(shown, [])

    def test_libraries_present(self):
        listener = Listener(importer=lambda name: object())
        self.assertEqual(listener.check_libraries(), (True, ""))


if __name__ == "__main__":
    unittest.main()
