import inspect
import unittest

from assistant.commands import Reply
from assistant.listen import ListenResult, Listener
from assistant.ui.bridge import Bridge, short_caption


class Signal:
    def __init__(self, log, name):
        self.log, self.name = log, name

    def emit(self, *args):
        self.log.append((self.name,) + args)


class FakeBus:
    def __init__(self):
        self.log = []

    def __getattr__(self, name):
        return Signal(self.log, name)

    def names(self):
        return [entry[0] for entry in self.log]


class FakeProc:
    def __init__(self, polls):
        self.polls = list(polls)

    def poll(self):
        return self.polls.pop(0) if len(self.polls) > 1 else self.polls[0]


class FakeSpeaker:
    def __init__(self, enabled):
        self.enabled, self._proc, self.spoken = enabled, None, []

    def supported(self):
        return True

    def speak(self, text):
        if not self.enabled:
            return False
        self.spoken.append(text)
        self._proc = FakeProc([None, None, 0])
        return True

    def stop(self):
        self._proc = None


class FakeRouter:
    pending = None

    def handle(self, text):
        if "secret" in text:
            return Reply("'secret thing' is not on my approved list.")
        return Reply("Asked your computer to open Safari.")


class FakeListener:
    def __init__(self, result, levels=(0.02, 0.05)):
        self.result, self.levels = result, levels

    def listen_once(self, show, on_level=None):
        show("Listening... the microphone is ON.")
        for level in self.levels:
            if on_level:
                on_level(level)
        show("Microphone is OFF.")
        return self.result


def make(speech_on=True, listener=None):
    bus = FakeBus()
    speaker = FakeSpeaker(speech_on)
    bridge = Bridge(bus, FakeRouter(), speaker, listener, poll_interval=0)
    return bus, speaker, bridge


class BridgeTests(unittest.TestCase):
    def test_unapproved_app_fails_and_never_speaks(self):
        bus, speaker, bridge = make()
        bridge.handle_text("open secret thing")
        self.assertEqual(bus.names(), ["processing_started", "caption_changed", "task_failed"])
        self.assertEqual(speaker.spoken, [])

    def test_success_flows_processing_speaking_completed(self):
        bus, speaker, bridge = make(speech_on=True)
        bridge.handle_text("open safari")
        self.assertEqual(
            bus.names(),
            ["processing_started", "caption_changed", "speaking_started",
             "speaking_finished", "task_completed"],
        )

    def test_speech_off_means_no_speaking_animation(self):
        bus, speaker, bridge = make(speech_on=False)
        bridge.handle_text("open safari")
        self.assertNotIn("speaking_started", bus.names())
        self.assertEqual(bus.names()[-1], "task_completed")

    def test_listening_only_when_mic_audio_arrives(self):
        listener = FakeListener(ListenResult(None, "I did not hear anything."), levels=())
        bus, _, bridge = make(listener=listener)
        bridge.listen_and_handle()
        self.assertNotIn("listening_started", bus.names())
        self.assertEqual(bus.names()[-1], "task_failed")

    def test_listening_starts_once_and_levels_are_0_to_1(self):
        listener = FakeListener(ListenResult("open safari", None))
        bus, _, bridge = make(listener=listener)
        bridge.listen_and_handle()
        self.assertEqual(bus.names().count("listening_started"), 1)
        self.assertLess(bus.names().index("listening_started"), bus.names().index("audio_level"))
        levels = [e[1] for e in bus.log if e[0] == "audio_level"]
        self.assertTrue(levels and all(0.0 <= v <= 1.0 for v in levels))

    def test_mic_off_starts_thinking_before_transcript(self):
        listener = FakeListener(ListenResult("open safari", None))
        bus, _, bridge = make(listener=listener)
        bridge.listen_and_handle()
        names = bus.names()
        self.assertLess(names.index("processing_started"), names.index("transcript_updated"))
        self.assertEqual(names[-1], "task_completed")

    def test_caption_is_one_short_line(self):
        self.assertLessEqual(len(short_caption("word " * 40)), 60)
        self.assertEqual(short_caption("first\nsecond"), "first")

    def test_listener_accepts_level_callback(self):
        self.assertIn("on_level", inspect.signature(Listener.listen_once).parameters)


if __name__ == "__main__":
    unittest.main()
