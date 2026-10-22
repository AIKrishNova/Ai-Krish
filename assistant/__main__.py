"""Start the assistant with:  python3 -m assistant"""
from assistant.commands import Router
from assistant.config import db_path
from assistant.desktop import Desktop
from assistant.speech import Speaker, handle_speech_command
from assistant.storage import NoteStore


def main():
    speaker = Speaker()
    router = Router(NoteStore(db_path()), Desktop())
    print("AI Krish assistant v1 (typed commands). Type 'help' for examples, 'exit' to quit.")
    print("Spoken replies are off. Type 'speak on' to turn them on.")
    try:
        while True:
            try:
                line = input("you> ")
            except (EOFError, KeyboardInterrupt):
                print()
                break
            handled = handle_speech_command(line, speaker)
            if handled is not None:
                text, say_it = handled
                router.pending = None  # a speech command cancels any waiting delete question
                print("krish> " + text)
                if say_it:
                    speaker.speak(text)
                continue
            reply = router.handle(line)
            print("krish> " + reply.text)
            if reply.quit:
                break
            speaker.speak(reply.text)
    finally:
        speaker.stop()


if __name__ == "__main__":
    main()
