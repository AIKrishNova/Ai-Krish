"""UI-free command runner, so it can be tested without PySide6."""
from assistant.reminders import handle_reminder_command
from assistant.speech import handle_speech_command


def run_command(line, router, speaker, reminders):
    """Run one typed or heard command. Returns (reply_text, should_quit)."""
    handled = handle_speech_command(line, speaker)
    if handled is not None:
        text, say_it = handled
        router.pending = None  # a speech command cancels any waiting delete question
        if say_it:
            speaker.speak(text)
        return text, False
    text = handle_reminder_command(line, reminders)
    if text is not None:
        speaker.speak(text)
        return text, False
    reply = router.handle(line)
    if not reply.quit:
        speaker.speak(reply.text)
    return reply.text, reply.quit
