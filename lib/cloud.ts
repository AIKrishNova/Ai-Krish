/* eslint-disable @typescript-eslint/no-explicit-any */
// Cloud copy of chats and settings, stored in the user's own Supabase rows (see supabase/chat-sync.sql).
// Row Level Security does the access control; this file only uses the public (publishable) key.
// Every function returns a result instead of throwing, so the app keeps working from local storage if the cloud is unavailable.
import { createClient } from "./supabase/client";

export type CloudChat = { id: string; title: string; updated: number; messages: any[] };
export type CloudSettings = { instructions: string; notes: string[]; done: number[]; updated: number };
type Fail = { ok: false; error: string };

function msg(e: unknown) {
  return e instanceof Error ? e.message : String(e);
}

async function userId(): Promise<string | null> {
  try {
    const { data } = await createClient().auth.getUser();
    return data?.user?.id ?? null;
  } catch {
    return null;
  }
}

/** True when the error means the SQL has not been run yet. */
export function tableMissing(error: string) {
  return /relation .* does not exist|schema cache|Could not find the table/i.test(error);
}

export async function pullChats(): Promise<{ ok: true; chats: CloudChat[] } | Fail> {
  try {
    const { data, error } = await createClient()
      .from("chats")
      .select("id,title,updated_at,messages")
      .order("updated_at", { ascending: false })
      .limit(60);
    if (error) return { ok: false, error: error.message };
    return {
      ok: true,
      chats: (data ?? []).map((r: any) => ({
        id: String(r.id),
        title: String(r.title ?? "New chat"),
        updated: new Date(r.updated_at).getTime() || 0,
        messages: Array.isArray(r.messages) ? r.messages : [],
      })),
    };
  } catch (e) {
    return { ok: false, error: msg(e) };
  }
}

export async function pushChats(chats: CloudChat[]): Promise<{ ok: true } | Fail> {
  if (chats.length === 0) return { ok: true };
  try {
    const uid = await userId();
    if (!uid) return { ok: false, error: "Not signed in." };
    const rows = chats.map((c) => ({
      user_id: uid,
      id: c.id,
      title: c.title.slice(0, 120),
      messages: c.messages.slice(-60),
      updated_at: new Date(c.updated || Date.now()).toISOString(),
    }));
    const { error } = await createClient().from("chats").upsert(rows, { onConflict: "user_id,id" });
    return error ? { ok: false, error: error.message } : { ok: true };
  } catch (e) {
    return { ok: false, error: msg(e) };
  }
}

export async function removeChat(id: string): Promise<{ ok: true } | Fail> {
  try {
    const uid = await userId();
    if (!uid) return { ok: false, error: "Not signed in." };
    const { error } = await createClient().from("chats").delete().eq("user_id", uid).eq("id", id);
    return error ? { ok: false, error: error.message } : { ok: true };
  } catch (e) {
    return { ok: false, error: msg(e) };
  }
}

export async function removeAllChats(): Promise<{ ok: true } | Fail> {
  try {
    const uid = await userId();
    if (!uid) return { ok: false, error: "Not signed in." };
    const { error } = await createClient().from("chats").delete().eq("user_id", uid);
    return error ? { ok: false, error: error.message } : { ok: true };
  } catch (e) {
    return { ok: false, error: msg(e) };
  }
}

export async function pullSettings(): Promise<{ ok: true; settings: CloudSettings | null } | Fail> {
  try {
    const { data, error } = await createClient()
      .from("user_settings")
      .select("instructions,notes,done,updated_at")
      .maybeSingle();
    if (error) return { ok: false, error: error.message };
    if (!data) return { ok: true, settings: null };
    const r: any = data;
    return {
      ok: true,
      settings: {
        instructions: String(r.instructions ?? ""),
        notes: Array.isArray(r.notes) ? r.notes.map(String) : [],
        done: Array.isArray(r.done) ? r.done.map(Number).filter((n: number) => Number.isFinite(n)) : [],
        updated: new Date(r.updated_at).getTime() || 0,
      },
    };
  } catch (e) {
    return { ok: false, error: msg(e) };
  }
}

export async function pushSettings(s: { instructions: string; notes: string[]; done: number[] }): Promise<{ ok: true } | Fail> {
  try {
    const uid = await userId();
    if (!uid) return { ok: false, error: "Not signed in." };
    const { error } = await createClient()
      .from("user_settings")
      .upsert({ user_id: uid, instructions: s.instructions.slice(0, 1500), notes: s.notes.slice(-30), done: s.done, updated_at: new Date().toISOString() }, { onConflict: "user_id" });
    return error ? { ok: false, error: error.message } : { ok: true };
  } catch (e) {
    return { ok: false, error: msg(e) };
  }
}
