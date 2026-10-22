"""Turns typed text into actions. Rule-based for now (no AI yet)."""
import re
from dataclasses import dataclass

from assistant import config
from assistant.desktop import clean_name

WAKE = re.compile(r"^(?:(?:hey|hi|ok|okay)\s+)?(?:krish|jarvis)\b[\s,:\-]*", re.IGNORECASE)

HELP = """AI Krish assistant (version 1, typed commands)

Notes:
  take a note: buy groceries tomorrow
  list notes            |  read latest note  |  read note 3
  find notes python     |  find my python notes
  delete note 3         (asks yes/no first)
  export notes          (saves a Markdown file)
Clipboard:
  copy latest note      |  copy note 3  |  copy text: hello
Open things (approved list only):
  open safari  |  open gmail  |  open downloads  |  open https://example.com
Other: help, exit
Tip: you can start with "Hey Krish," if you like. Type "speak on" to hear replies."""


@dataclass
class Reply:
    text: str
    quit: bool = False


def _short_date(note):
    return note["created_at"][:16].replace("T", " ")


def _lines(notes):
    return "\n".join("#%d  %s  %s" % (n["id"], _short_date(n), n["title"]) for n in notes)


class Router:
    def __init__(self, store, desktop):
        self.store = store
        self.desktop = desktop
        self.pending = None
        flags = re.IGNORECASE
        self._routes = [
            (re.compile(r"(?:help|commands|what can you do)\??", flags), self._help),
            (re.compile(r"(?:exit|quit|bye|goodbye)", flags), self._quit),
            (re.compile(r"stop\s+(?:speaking|listening)", flags), self._no_voice),
            (re.compile(r"(?:take|make|add|save|write)\s+(?:a\s+)?note\b(?:\s*[:\-]\s*|\s+)?(.*)", flags), self._add_note),
            (re.compile(r"note\s*:\s*(.+)", flags), self._add_note),
            (re.compile(r"(?:read|show|open|view|get)\s+(?:my\s+)?(?:latest|last|newest)\s+note", flags), self._latest),
            (re.compile(r"(?:read|show|open|view)\s+note\s+#?(\d+)", flags), self._read),
            (re.compile(r"(?:(?:list|show|open|view)\s+(?:all\s+)?)?(?:my\s+)?notes", flags), self._list),
            (re.compile(r"(?:find|search)\s+(?:my\s+)?notes?\s+(?:for\s+|about\s+)?(.+)", flags), self._search),
            (re.compile(r"(?:find|search)\s+(?:for\s+)?(?:my\s+)?(.+?)\s+notes", flags), self._search),
            (re.compile(r"(?:delete|remove)\s+note\s+#?(\d+)", flags), self._delete),
            (re.compile(r"copy\s+(?:my\s+)?(?:latest|last|newest)\s+note", flags), self._copy_latest),
            (re.compile(r"copy\s+note\s+#?(\d+)", flags), self._copy_note),
            (re.compile(r"copy\s+(?:this\s+)?text\s*[:\-]?\s*(.+)", flags), self._copy_text),
            (re.compile(r"export\s+(?:my\s+)?notes", flags), self._export),
            (re.compile(r"(?:please\s+)?open\s+(.+)", flags), self._open),
        ]

    def handle(self, raw):
        text = WAKE.sub("", (raw or "").strip(), count=1).strip()
        if not text:
            return Reply("Type a command, or 'help'.")
        note = ""
        if self.pending is not None:
            pending, self.pending = self.pending, None
            answer = text.lower().rstrip(".!")
            if answer in ("yes", "y"):
                return self._confirm(pending)
            if answer in ("no", "n"):
                return Reply("Okay, cancelled. Nothing was deleted.")
            note = "(Delete cancelled.) "
        try:
            reply = self._dispatch(text)
        except Exception as exc:  # keep the assistant alive on any error
            reply = Reply("Sorry, something went wrong: %s" % exc)
        reply.text = note + reply.text
        return reply

    def _dispatch(self, text):
        for pattern, handler in self._routes:
            match = pattern.fullmatch(text)
            if match:
                return handler(match)
        return Reply(
            "I don't know that command yet. Version 1 understands notes, opening "
            "approved apps/websites/folders, and the clipboard. Type 'help' for examples."
        )

    def _confirm(self, pending):
        if pending["action"] == "delete":
            if self.store.delete(pending["id"]):
                return Reply("Deleted note #%d." % pending["id"])
            return Reply("Note #%d was not found." % pending["id"])
        return Reply("Nothing to confirm.")

    def _help(self, m):
        return Reply(HELP)

    def _quit(self, m):
        return Reply("Goodbye!", quit=True)

    def _no_voice(self, m):
        return Reply("Voice is not part of version 1 yet, so there is nothing to stop.")

    def _add_note(self, m):
        body = (m.group(1) or "").strip()
        if not body:
            return Reply("What should the note say? Try: take a note: buy groceries tomorrow")
        note_id = self.store.add(body)
        return Reply("Saved note #%d." % note_id)

    def _latest(self, m):
        note = self.store.latest()
        if note is None:
            return Reply("You have no notes yet.")
        return Reply(self._format(note))

    def _read(self, m):
        note = self.store.get(int(m.group(1)))
        if note is None:
            return Reply("I could not find note #%s." % m.group(1))
        return Reply(self._format(note))

    def _format(self, note):
        return "Note #%d - %s\n%s\n\n%s" % (note["id"], note["title"], _short_date(note), note["body"])

    def _list(self, m):
        notes = self.store.list(20)
        if not notes:
            return Reply("You have no notes yet. Try: take a note: buy groceries tomorrow")
        return Reply("Your latest notes:\n" + _lines(notes))

    def _search(self, m):
        term = m.group(1).strip()
        notes = self.store.search(term)
        if not notes:
            return Reply("No notes found for '%s'." % term)
        return Reply("Notes matching '%s':\n%s" % (term, _lines(notes)))

    def _delete(self, m):
        note_id = int(m.group(1))
        note = self.store.get(note_id)
        if note is None:
            return Reply("I could not find note #%d." % note_id)
        self.pending = {"action": "delete", "id": note_id}
        return Reply("Delete note #%d (%s)? This cannot be undone. Type yes or no." % (note_id, note["title"]))

    def _copy_latest(self, m):
        note = self.store.latest()
        if note is None:
            return Reply("You have no notes yet.")
        return Reply(self.desktop.copy_text(note["body"]).message)

    def _copy_note(self, m):
        note = self.store.get(int(m.group(1)))
        if note is None:
            return Reply("I could not find note #%s." % m.group(1))
        return Reply(self.desktop.copy_text(note["body"]).message)

    def _copy_text(self, m):
        return Reply(self.desktop.copy_text(m.group(1)).message)

    def _export(self, m):
        path, count = self.store.export_markdown(config.data_dir() / "exports")
        if path is None:
            return Reply("You have no notes to export.")
        return Reply("Exported %d notes to %s" % (count, path))

    def _open(self, m):
        target = m.group(1).strip().rstrip(".!?")
        if target.lower().startswith(("http://", "https://")):
            return Reply(self.desktop.open_website(target).message)
        key = clean_name(target)
        if key in config.SITES:
            return Reply(self.desktop.open_website(key).message)
        if key in config.APPS:
            return Reply(self.desktop.open_app(key).message)
        if key in config.FOLDERS:
            return Reply(self.desktop.open_folder(key).message)
        return Reply(
            "'%s' is not on my approved list.\nApps: %s\nWebsites: %s\nFolders: %s"
            % (
                target,
                ", ".join(sorted(config.APPS)),
                ", ".join(sorted(config.SITES)),
                ", ".join(sorted(config.FOLDERS)),
            )
        )
