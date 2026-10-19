"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { FOCUS, Icon } from "../../components/Sidebar";
import { pullChats, removeChat, tableMissing, type CloudChat } from "../../lib/cloud";
import { chatToText, forgetLocalChat, matchesQuery, previewOf, savingEnabled, stashForChat } from "../../lib/history";

type Load = { kind: "loading" } | { kind: "ready" } | { kind: "setup" } | { kind: "error"; message: string };

function download(name: string, text: string, type: string) {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

const fileSafe = (s: string) => s.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "").slice(0, 40).toLowerCase() || "chat";

export default function HistoryPage() {
  const [chats, setChats] = useState<CloudChat[]>([]);
  const [load, setLoad] = useState<Load>({ kind: "loading" });
  const [query, setQuery] = useState("");
  const [openId, setOpenId] = useState<string | null>(null);
  const [saving, setSaving] = useState(true);

  async function refresh() {
    setLoad({ kind: "loading" });
    const r = await pullChats();
    if (r.ok) {
      setChats(r.chats);
      setLoad({ kind: "ready" });
    } else {
      setLoad(tableMissing(r.error) ? { kind: "setup" } : { kind: "error", message: r.error });
    }
  }

  useEffect(() => {
    document.title = "Chat history · AI KRISH";
    try { setSaving(savingEnabled(localStorage)); } catch {}
    refresh();
  }, []);

  const shown = useMemo(() => chats.filter((c) => matchesQuery(c, query)), [chats, query]);

  async function remove(c: CloudChat) {
    if (!window.confirm(`Delete "${c.title}" from your database? This cannot be undone.`)) return;
    const r = await removeChat(c.id);
    if (!r.ok) { window.alert("Could not delete it: " + r.error); return; }
    try { forgetLocalChat(localStorage, c.id); } catch {}
    setChats((cs) => cs.filter((x) => x.id !== c.id));
    if (openId === c.id) setOpenId(null);
  }

  function openInChat(c: CloudChat) {
    try { stashForChat(localStorage, c); } catch {}
    window.location.assign("/?chat=" + encodeURIComponent(c.id));
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-slate-50 text-slate-900">
      <header className="sticky top-0 z-10 border-b border-slate-100 bg-white/85 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center gap-3 px-4 py-3">
          <Link href="/" className={`flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm text-slate-600 hover:bg-slate-100 ${FOCUS}`}>
            <Icon n="left" size={16} /> Back to chat
          </Link>
          <h1 className="ml-1 text-base font-bold tracking-wide">Chat history</h1>
          <button onClick={refresh} className={`ml-auto flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 ${FOCUS}`}>
            <Icon n="refresh" size={15} /> Refresh
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 py-5">
        {!saving && (
          <div role="status" className="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
            Saving to the database is switched off, so new chats are not being added here. Turn it back on in Settings on the chat page. Chats already saved are still listed below.
          </div>
        )}

        <label className="relative mb-4 block">
          <span className="sr-only">Search saved chats</span>
          <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"><Icon n="search" size={16} /></span>
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search titles and messages..."
            className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-9 pr-3 text-sm outline-none placeholder:text-slate-400 focus:border-violet-400" />
        </label>

        {load.kind === "loading" && <p className="py-10 text-center text-sm text-slate-500" role="status">Loading your saved chats...</p>}

        {load.kind === "setup" && (
          <div role="alert" className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-700">
            <div className="font-medium">The database tables are not created yet.</div>
            <p className="mt-1 text-slate-600">Open the Supabase dashboard, go to SQL Editor, paste the contents of <code>supabase/chat-sync.sql</code> and click Run. Then press Refresh.</p>
          </div>
        )}

        {load.kind === "error" && (
          <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
            Could not load your chats: {load.message}
          </div>
        )}

        {load.kind === "ready" && (
          <>
            <div className="mb-3 flex items-center justify-between text-xs text-slate-500">
              <span>{shown.length} of {chats.length} saved chat{chats.length === 1 ? "" : "s"} (latest 60 shown)</span>
              {chats.length > 0 && (
                <button onClick={() => download("ai-krish-chats.json", JSON.stringify(chats, null, 2), "application/json")}
                  className={`rounded-lg border border-slate-200 px-2.5 py-1 text-slate-700 hover:bg-slate-50 ${FOCUS}`}>Export all (JSON)</button>
              )}
            </div>

            {chats.length === 0 && <p className="py-10 text-center text-sm text-slate-500">No saved chats yet. Chat with Krish and they will appear here.</p>}
            {chats.length > 0 && shown.length === 0 && <p className="py-10 text-center text-sm text-slate-500">No chats match your search.</p>}

            <ul className="space-y-2">
              {shown.map((c) => {
                const open = openId === c.id;
                return (
                  <li key={c.id} className="rounded-2xl border border-slate-200 bg-white shadow-sm">
                    <button onClick={() => setOpenId(open ? null : c.id)} aria-expanded={open} className={`flex w-full items-start gap-3 rounded-2xl px-4 py-3 text-left ${FOCUS}`}>
                      <div className="min-w-0 flex-1">
                        <div className="truncate text-sm font-semibold">{c.title}</div>
                        <div className="mt-0.5 truncate text-xs text-slate-500">{previewOf(c) || "Empty chat"}</div>
                      </div>
                      <div className="flex-none text-right text-xs text-slate-400">
                        <div>{new Date(c.updated).toLocaleDateString()}</div>
                        <div>{c.messages.length} msg</div>
                      </div>
                    </button>

                    {open && (
                      <div className="border-t border-slate-100 px-4 py-3">
                        <div className="mb-3 flex flex-wrap gap-2">
                          <button onClick={() => openInChat(c)} className={`rounded-lg bg-violet-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-violet-700 ${FOCUS}`}>Open in chat</button>
                          <button onClick={() => download(`${fileSafe(c.title)}.txt`, chatToText(c), "text/plain")} className={`rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 ${FOCUS}`}>Export .txt</button>
                          <button onClick={() => remove(c)} className={`ml-auto rounded-lg border border-red-200 px-3 py-1.5 text-sm text-red-700 hover:bg-red-50 ${FOCUS}`}>Delete</button>
                        </div>
                        <ol className="max-h-[28rem] space-y-2 overflow-y-auto pr-1">
                          {c.messages.map((m, i) => {
                            const mine = m?.role === "user";
                            const n = Array.isArray(m?.images) ? m.images.length : 0;
                            return (
                              <li key={i} className={`rounded-xl px-3 py-2 text-sm ${mine ? "bg-violet-50 text-slate-900" : "bg-slate-50 text-slate-800"}`}>
                                <div className="mb-0.5 text-[11px] font-semibold uppercase tracking-wide text-slate-500">{mine ? "You" : "Krish"}</div>
                                <div className="whitespace-pre-wrap break-words">{typeof m?.text === "string" ? m.text : ""}</div>
                                {n > 0 && <div className="mt-1 text-xs text-slate-500">{n} photo{n === 1 ? "" : "s"} attached</div>}
                              </li>
                            );
                          })}
                        </ol>
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          </>
        )}
      </main>
    </div>
  );
}
