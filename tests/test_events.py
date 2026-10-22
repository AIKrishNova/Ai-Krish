import unittest

from assistant.events import EVENTS, EventBus


class EventBusTests(unittest.TestCase):
    def test_listener_receives_event_and_data(self):
        bus, seen = EventBus(), []
        bus.subscribe(lambda name, data: seen.append((name, data)))
        bus.emit("transcript_updated", text="open safari")
        self.assertEqual(seen, [("transcript_updated", {"text": "open safari"})])

    def test_unknown_event_is_rejected(self):
        with self.assertRaises(ValueError):
            EventBus().emit("made_up")

    def test_broken_listener_does_not_stop_others(self):
        bus, seen = EventBus(), []
        bus.subscribe(lambda n, d: 1 / 0)
        bus.subscribe(lambda n, d: seen.append(n))
        bus.emit("wake_detected")
        self.assertEqual(seen, ["wake_detected"])

    def test_all_nine_events_defined(self):
        self.assertEqual(len(EVENTS), 9)


if __name__ == "__main__":
    unittest.main()
