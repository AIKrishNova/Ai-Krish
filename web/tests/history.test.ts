import { describe, expect, it } from "vitest";
import { chatToText, forgetLocalChat, matchesQuery, previewOf, savingEnabled, stashForChat, LOCAL_CHATS_KEY } from "../lib/history";

const chat = (id: string, title = "Linux help", extra: object[] = []) => ({
  id, title, updated: 1_700_000_000_000,
  messages: [{ role: "user", text: "How do I list files?" }, { role: "jarvis", text: "Use ls -la." }, ...extra],
});

function store(initial: Record<string, string> = {}) {
  const d = { ...initial };
  return { d, getItem: (k: string) => d[k] ?? null, setItem: (k: string, v: string) => { d[k] = v; } };
}

describe("history helpers", () => {
  it("searches titles and message text, case-insensitively", () => {
    expect(matchesQuery(chat("1"), "")).toBe(true);
    expect(matchesQuery(chat("1"), "LINUX")).toBe(true);
    expect(matchesQuery(chat("1"), "ls -la")).toBe(true);
    expect(matchesQuery(chat("1"), "python")).toBe(false);
  });

  it("previews the first user message and truncates", () => {
    expect(previewOf(chat("1"))).toBe("How do I list files?");
    const long = { ...chat("2"), messages: [{ role: "user", text: "x".repeat(300) }] };
    expect(previewOf(long, 20)).toHaveLength(20);
    expect(previewOf({ ...chat("3"), messages: [] })).toBe("");
  });

  it("exports a readable text copy", () => {
    const t = chatToText(chat("1", "T", [{ role: "user", text: "see", images: ["a", "b"] }]));
    expect(t).toContain("You: How do I list files?");
    expect(t).toContain("Krish: Use ls -la.");
    expect(t).toContain("[2 photos]");
  });

  it("saving is on unless Settings switched it off", () => {
    expect(savingEnabled(store())).toBe(true);
    expect(savingEnabled(store({ "krish-cloud": "1" }))).toBe(true);
    expect(savingEnabled(store({ "krish-cloud": "0" }))).toBe(false);
  });

  it("stashes a chat first, replacing an older copy, and forgets it again", () => {
    const s = store({ [LOCAL_CHATS_KEY]: JSON.stringify([{ id: "a", title: "old", updated: 1, messages: [] }, { id: "b", title: "b", updated: 1, messages: [] }]) });
    stashForChat(s, chat("b", "new b"));
    const after = JSON.parse(s.d[LOCAL_CHATS_KEY]);
    expect(after.map((c: { id: string }) => c.id)).toEqual(["b", "a"]);
    expect(after[0].title).toBe("new b");
    forgetLocalChat(s, "b");
    expect(JSON.parse(s.d[LOCAL_CHATS_KEY]).map((c: { id: string }) => c.id)).toEqual(["a"]);
  });

  it("survives corrupt local data", () => {
    const s = store({ [LOCAL_CHATS_KEY]: "{not json" });
    stashForChat(s, chat("z"));
    expect(JSON.parse(s.d[LOCAL_CHATS_KEY])).toHaveLength(1);
  });
});
