"""Start the assistant with:  python3 -m assistant
For voice input, start it with:  ~/.ai-krish/venv/bin/python -m assistant
"""
from assistant.commands import Router
from assistant.config import db_path
from assistant.desktop import Desktop
from assistant.listen import Listener, is_listen_command, is_stop_listening_command
from assistant.reminders import Reminders, handle_reminder_command
from assistant.speech import Speaker, handle_speech_command
from assistant.storage import NoteStore


def process(line, router, speaker, reminders):
    """Run one command, typed or heard. Returns True if the assistant should quit."""
    handled = handle_speech_command(line, speaker)
    if handled is not None:
        text, say_it = handled
        router.pending = None  # a speech command cancels any waiting delete question
        print("krish> " + text)
        if say_it:
            speaker.speak(text)
        return False
    reminder_text = handle_reminder_command(line, reminders)
    if reminder_text is not None:
        router.pending = None  # a reminder command cancels any waiting delete question
        print("krish> " + reminder_text)
        speaker.speak(reminder_text)
        return False
    reply = router.handle(line)
    print("krish> " + reply.text)
    if reply.quit:
        return True
    speaker.speak(reply.text)
    return False


def make_notifier(speaker):
    """Called from a timer thread when a reminder or timer fires."""
    def notify(text):
        print("\nkrish> " + text)
        print("you> ", end="", flush=True)  # bring the prompt back
        speaker.speak(text)
    return notify


def main():
    speaker = Speaker()
    listener = Listener()
    router = Router(NoteStore(db_path()), Desktop())
    reminders = Reminders(make_notifier(speaker))
    print("AI Krish assistant v1. Type 'help' for examples, 'exit' to quit.")
    print("Spoken replies are off ('speak on'). Type 'listen' to talk to me.")
    try:
        while True:
            try:
                line = input("you> ")
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if is_stop_listening_command(line):
                print("krish> I only listen after you type 'listen', so I am not listening now.")
                continue
            if is_listen_command(line):
                speaker.stop()
                router.pending = None  # a voice request can never answer a waiting yes/no
                result = listener.listen_once(lambda message: print("krish> " + message))
                if result.text is None:
                    print("krish> " + result.error)
                    continue
                print("you (voice)> " + result.text)
                if process(result.text, router, speaker, reminders):
                    break
                continue
            if process(line, router, speaker, reminders):
                break
    finally:
        reminders.stop()
        speaker.stop()


if __name__ == "__main__":
    main()
