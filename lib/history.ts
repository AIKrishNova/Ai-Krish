/* eslint-disable @typescript-eslint/no-explicit-any */
// Helpers for the History page: searching, previewing, exporting, and handing a saved chat back to the main app.
import type { CloudChat } from "./cloud";

export const LOCAL_CHATS_KEY = "krish-chats";
export const LOCAL_CLOUD_KEY = "krish-cloud";

type StorageLike = Pick<Storage, "getItem" | "setItem">;

const who = (role: unknown) => (role === "user" ? "You" : "Krish");
const textOf = (m: any) => (typeof m?.text === "string" ? m.text : "");

/** Lower-case search over the title and every message. An empty query matches everything. */
export function matchesQuery(c: CloudChat, query: string): boolean {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  if (c.title.toLowerCase().includes(q)) return true;
  return c.messages.some((m) => textOf(m).toLowerCase().includes(q));
}

/** One short line describing a chat: the first thing the user asked. */
export function previewOf(c: CloudChat, max = 140): string {
  const first = c.messages.find((m) => m?.role === "user" && textOf(m).trim()) ?? c.messages.find((m) => textOf(m).trim());
  const t = first ? textOf(first).replace(/\s+/g, " ").trim() : "";
  return t.length > max ? t.slice(0, max - 1) + "…" : t;
}

/** A plain-text copy of one chat, for the Export button. */
export function chatToText(c: CloudChat): string {
  const lines = [c.title, new Date(c.updated).toLocaleString(), ""];
  for (const m of c.messages) {
    const n = Array.isArray(m?.images) ? m.images.length : 0;
    lines.push(`${who(m?.role)}: ${textOf(m)}${n ? ` [${n} photo${n === 1 ? "" : "s"}]` : ""}`, "");
  }
  return lines.join("\n").trimEnd() + "\n";
}

/** True unless the person switched database saving off in Settings. */
export function savingEnabled(storage: Pick<Storage, "getItem">): boolean {
  try {
    return storage.getItem(LOCAL_CLOUD_KEY) !== "0";
  } catch {
    return true;
  }
}

function readLocal(storage: StorageLike): any[] {
  try {
    const arr = JSON.parse(storage.getItem(LOCAL_CHATS_KEY) || "[]");
    return Array.isArray(arr) ? arr : [];
  } catch {
    return [];
  }
}

/** Put a chat first in this browser's list so the main page can open it (replaces an older copy of the same chat). */
export function stashForChat(storage: StorageLike, c: CloudChat): void {
  const rest = readLocal(storage).filter((x) => x && x.id !== c.id);
  storage.setItem(LOCAL_CHATS_KEY, JSON.stringify([{ id: c.id, title: c.title, updated: c.updated, messages: c.messages }, ...rest].slice(0, 40)));
}

/** Drop a chat from this browser's list so it is not uploaded again after being deleted from the database. */
export function forgetLocalChat(storage: StorageLike, id: string): void {
  storage.setItem(LOCAL_CHATS_KEY, JSON.stringify(readLocal(storage).filter((x) => x && x.id !== id)));
}
