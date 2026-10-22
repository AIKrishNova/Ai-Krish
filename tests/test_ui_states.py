import unittest

from assistant.ui.states import (
    ERROR, IDLE, LISTENING, SPEAKING, THINKING, WAKE, next_state,
)


def walk(events, start=IDLE):
    state, seen = start, []
    for event in events:
        state = next_state(state, event)
        seen.append(state)
    return seen


class StateRuleTests(unittest.TestCase):
    def test_happy_path(self):
        seen = walk([
            "wake_detected", "listening_started", "processing_started",
            "speaking_started", "speaking_finished", "task_completed",
        ])
        self.assertEqual(seen, [WAKE, LISTENING, THINKING, SPEAKING, SPEAKING, IDLE])

    def test_failure_goes_to_error(self):
        self.assertEqual(walk(["processing_started", "task_failed"])[-1], ERROR)

    def test_cancel_returns_to_idle(self):
        self.assertEqual(walk(["listening_started", "task_cancelled"])[-1], IDLE)

    def test_level_and_transcript_do_not_change_state(self):
        self.assertEqual(walk(["audio_level", "transcript_updated"], LISTENING), [LISTENING, LISTENING])

    def test_unknown_event_is_rejected(self):
        with self.assertRaises(ValueError):
            next_state(IDLE, "made_up")


if __name__ == "__main__":
    unittest.main()
