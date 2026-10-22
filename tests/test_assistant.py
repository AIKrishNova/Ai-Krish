import tempfile
import unittest
from pathlib import Path

from assistant.commands import Router
from assistant.desktop import Desktop, Result
from assistant.storage import NoteStore


class FakeProc:
    def __init__(self, returncode=0):
        self.returncode = returncode


class FakeDesktop:
    def __init__(self):
        self.calls = []

    def open_app(self, name):
        self.calls.append(("app", name))
        return Result(True, "Opened app " + name)

    def open_folder(self, name):
        self.calls.append(("folder", name))
        return Result(True, "Opened folder " + name)

    def open_website(self, name):
        self.calls.append(("site", name))
        return Result(True, "Opened site " + name)

    def copy_text(self, text):
        self.calls.append(("copy", text))
        return Result(True, "Copied to the clipboard.")


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = NoteStore(Path(self.tmp.name) / "test.db")

    def test_add_get_latest_list(self):
        first = self.store.add("buy groceries tomorrow")
        second = self.store.add("python practice")
        self.assertEqual(self.store.get(first)["body"], "buy groceries tomorrow")
        self.assertEqual(self.store.latest()["id"], second)
        self.assertEqual([n["id"] for n in self.store.list()], [second, first])

    def test_empty_note_rejected(self):
        with self.assertRaises(ValueError):
            self.store.add("   ")

    def test_search_and_special_characters(self):
        self.store.add("learn Python basics")
        self.store.add("100% done")
        self.assertEqual(len(self.store.search("python")), 1)
        self.assertEqual(len(self.store.search("%")), 1)
        self.assertEqual(self.store.search("zzz"), [])

    def test_delete(self):
        note_id = self.store.add("temp")
        self.assertTrue(self.store.delete(note_id))
        self.assertFalse(self.store.delete(note_id))

    def test_export_markdown(self):
        self.store.add("export me")
        path, count = self.store.export_markdown(Path(self.tmp.name) / "out")
        self.assertEqual(count, 1)
        self.assertIn("export me", path.read_text(encoding="utf-8"))


class DesktopTests(unittest.TestCase):
    def test_mac_open_app_uses_argument_list(self):
        calls = []

        def fake_run(args, **kwargs):
            calls.append(args)
            return FakeProc(0)

        result = Desktop(platform="mac", runner=fake_run).open_app("safari")
        self.assertTrue(result.ok)
        self.assertEqual(calls[0], ["open", "-a", "Safari"])

    def test_unknown_app_is_refused(self):
        calls = []
        desk = Desktop(platform="mac", runner=lambda args, **kw: calls.append(args))
        self.assertFalse(desk.open_app("rm -rf /").ok)
        self.assertEqual(calls, [])

    def test_app_missing_on_this_platform(self):
        desk = Desktop(platform="mac", runner=lambda args, **kw: FakeProc(0))
        self.assertFalse(desk.open_app("notepad").ok)

    def test_website_rules(self):
        opened = []
        desk = Desktop(platform="mac", browser_open=lambda url: opened.append(url) or True)
        self.assertFalse(desk.open_website("javascript:alert(1)").ok)
        self.assertFalse(desk.open_website("example.com").ok)
        self.assertEqual(opened, [])
        self.assertTrue(desk.open_website("gmail").ok)
        self.assertEqual(opened, ["https://mail.google.com"])

    def test_clipboard_mac(self):
        seen = {}

        def fake_run(args, **kwargs):
            seen["args"] = args
            seen["input"] = kwargs.get("input")
            return FakeProc(0)

        result = Desktop(platform="mac", runner=fake_run).copy_text("hello")
        self.assertTrue(result.ok)
        self.assertEqual(seen["args"], ["pbcopy"])
        self.assertEqual(seen["input"], b"hello")


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = NoteStore(Path(self.tmp.name) / "test.db")
        self.desk = FakeDesktop()
        self.router = Router(self.store, self.desk)

    def test_take_note_with_wake_phrase(self):
        reply = self.router.handle("Hey Krish, take a note: buy milk")
        self.assertIn("Saved note #1", reply.text)
        self.assertEqual(self.store.latest()["body"], "buy milk")

    def test_take_note_without_text_asks(self):
        reply = self.router.handle("take a note")
        self.assertIn("What should the note say", reply.text)
        self.assertIsNone(self.store.latest())

    def test_list_and_search(self):
        self.router.handle("take a note: python flask practice")
        self.assertIn("python flask", self.router.handle("open my notes").text)
        self.assertIn("python flask", self.router.handle("find my python notes").text)
        self.assertEqual(self.desk.calls, [])  # "open my notes" must not open an app

    def test_delete_needs_yes(self):
        self.router.handle("take a note: temp")
        self.assertIn("yes or no", self.router.handle("delete note 1").text)
        self.router.handle("no")
        self.assertIsNotNone(self.store.get(1))
        self.router.handle("delete note 1")
        self.assertIn("Deleted note #1", self.router.handle("yes").text)
        self.assertIsNone(self.store.get(1))

    def test_other_command_cancels_delete(self):
        self.router.handle("take a note: keep me")
        self.router.handle("delete note 1")
        self.router.handle("list notes")
        self.router.handle("yes")
        self.assertIsNotNone(self.store.get(1))

    def test_open_routing(self):
        self.router.handle("open safari")
        self.router.handle("open gmail")
        self.router.handle("open downloads")
        self.router.handle("open https://example.com")
        self.assertEqual(
            self.desk.calls,
            [("app", "safari"), ("site", "gmail"), ("folder", "downloads"), ("site", "https://example.com")],
        )

    def test_unapproved_open_is_refused(self):
        reply = self.router.handle("open secret thing")
        self.assertIn("not on my approved list", reply.text)
        self.assertEqual(self.desk.calls, [])

    def test_copy_latest_note(self):
        self.router.handle("take a note: copy this")
        self.router.handle("copy latest note")
        self.assertEqual(self.desk.calls, [("copy", "copy this")])

    def test_exit(self):
        self.assertTrue(self.router.handle("exit").quit)


if __name__ == "__main__":
    unittest.main()
