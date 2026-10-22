import unittest

from assistant.speech import Speaker, clean_for_speech, handle_speech_command


class FakeProc:
    def __init__(self):
        self.terminated = False

    def poll(self):
        return 0 if self.terminated else None

    def terminate(self):
        self.terminated = True


class FakePopen:
    def __init__(self):
        self.calls = []
        self.procs = []

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        proc = FakeProc()
        self.procs.append(proc)
        return proc


class CleanTests(unittest.TestCase):
    def test_links_become_the_word_link(self):
        self.assertEqual(clean_for_speech("Open https://example.com now"), "Open link now")

    def test_symbols_removed(self):
        self.assertEqual(clean_for_speech("**Hi** #1 `x`"), "Hi 1 x")

    def test_long_text_is_shortened(self):
        result = clean_for_speech("word " * 200)
        self.assertLessEqual(len(result), 301)
        self.assertTrue(result.endswith("."))

    def test_empty(self):
        self.assertEqual(clean_for_speech(""), "")
        self.assertEqual(clean_for_speech(None), "")


class SpeakerTests(unittest.TestCase):
    def test_disabled_never_speaks(self):
        fake = FakePopen()
        speaker = Speaker(platform="mac", popen=fake)
        self.assertFalse(speaker.speak("hi"))
        self.assertEqual(fake.calls, [])

    def test_mac_uses_argument_list(self):
        fake = FakePopen()
        speaker = Speaker(platform="mac", popen=fake, enabled=True)
        self.assertTrue(speaker.speak("hello there"))
        self.assertEqual(fake.calls[0][0], ["say", "-r", "185", "hello there"])

    def test_leading_dash_removed(self):
        fake = FakePopen()
        speaker = Speaker(platform="mac", popen=fake, enabled=True)
        speaker.speak("-rf hello")
        self.assertEqual(fake.calls[0][0][-1], "rf hello")

    def test_new_speech_stops_old(self):
        fake = FakePopen()
        speaker = Speaker(platform="mac", popen=fake, enabled=True)
        speaker.speak("one")
        speaker.speak("two")
        self.assertTrue(fake.procs[0].terminated)
        self.assertFalse(fake.procs[1].terminated)

    def test_stop(self):
        fake = FakePopen()
        speaker = Speaker(platform="mac", popen=fake, enabled=True)
        speaker.speak("one")
        speaker.stop()
        self.assertTrue(fake.procs[0].terminated)

    def test_failure_to_start_is_handled(self):
        def broken(args, **kwargs):
            raise OSError("no say command")

        speaker = Speaker(platform="mac", popen=broken, enabled=True)
        self.assertFalse(speaker.speak("hello"))

    def test_windows_passes_text_in_environment(self):
        fake = FakePopen()
        speaker = Speaker(platform="windows", popen=fake, enabled=True)
        self.assertTrue(speaker.speak("hello"))
        args, kwargs = fake.calls[0]
        self.assertEqual(args[0], "powershell")
        self.assertEqual(kwargs["env"]["AIKRISH_SPEECH_TEXT"], "hello")

    def test_unsupported_platform(self):
        speaker = Speaker(platform="other", popen=FakePopen(), enabled=True)
        self.assertFalse(speaker.speak("hello"))


class HandleTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakePopen()
        self.speaker = Speaker(platform="mac", popen=self.fake)

    def test_speak_on(self):
        text, say_it = handle_speech_command("speak on", self.speaker)
        self.assertTrue(self.speaker.enabled)
        self.assertTrue(say_it)
        self.assertIn("on", text)

    def test_wake_phrase_and_speak_off(self):
        self.speaker.enabled = True
        self.speaker.speak("talking")
        text, say_it = handle_speech_command("Hey Krish, speak off", self.speaker)
        self.assertFalse(self.speaker.enabled)
        self.assertFalse(say_it)
        self.assertTrue(self.fake.procs[0].terminated)

    def test_stop_keeps_speech_enabled(self):
        self.speaker.enabled = True
        self.speaker.speak("talking")
        text, say_it = handle_speech_command("stop speaking", self.speaker)
        self.assertTrue(self.fake.procs[0].terminated)
        self.assertTrue(self.speaker.enabled)
        self.assertFalse(say_it)

    def test_other_commands_are_ignored(self):
        self.assertIsNone(handle_speech_command("open safari", self.speaker))
        self.assertIsNone(handle_speech_command("take a note: stop speaking", self.speaker))

    def test_unsupported_platform_cannot_enable(self):
        speaker = Speaker(platform="other", popen=self.fake)
        text, say_it = handle_speech_command("speak on", speaker)
        self.assertFalse(speaker.enabled)
        self.assertFalse(say_it)


if __name__ == "__main__":
    unittest.main()
