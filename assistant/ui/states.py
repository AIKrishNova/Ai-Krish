"""Orb states and the rules for moving between them. No Qt needed."""

IDLE, WAKE, LISTENING, THINKING, SPEAKING, ERROR = (
    "idle", "wake", "listening", "thinking", "speaking", "error",
)

EVENT_NAMES = (
    "wake_detected",
    "listening_started",
    "audio_level",
    "transcript_updated",
    "processing_started",
    "speaking_started",
    "speaking_finished",
    "task_completed",
    "task_failed",
    "task_cancelled",
)

# Only events that change the orb appear here.
STATE_FOR_EVENT = {
    "wake_detected": WAKE,
    "listening_started": LISTENING,
    "processing_started": THINKING,
    "speaking_started": SPEAKING,
    "task_completed": IDLE,
    "task_failed": ERROR,
    "task_cancelled": IDLE,
}


def next_state(current, event):
    if event not in EVENT_NAMES:
        raise ValueError("Unknown event: %s" % event)
    return STATE_FOR_EVENT.get(event, current)
