"use client";

import { useRouter } from "next/navigation";
import { useState, type RefObject } from "react";
import { createClient } from "../lib/supabase/client";
import Logo from "./Logo";

export const FOCUS = "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500";

const P = {
  home: "M3 11l9-8 9 8v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z",
  chat: "M4 5h16v11H9l-5 4z",
  image: "M4 5h16v14H4z M4 16l5-5 4 4 3-3 4 4 M9 9.5h.01",
  file: "M6 3h8l4 4v14H6z M14 3v4h4",
  tools: "M4 4h6v6H4z M14 4h6v6h-6z M4 14h6v6H4z M14 14h6v6h-6z",
  tasks: "M5 4h14v16H5z M9 9h6 M9 13h6",
  memory: "M12 3a6 6 0 0 0-6 6c0 2 1 3 2 4v3h8v-3c1-1 2-2 2-4a6 6 0 0 0-6-6z M9 20h6",
  settings: "M12 9a3 3 0 1 0 .01 0z M12 2v3 M12 19v3 M2 12h3 M19 12h3 M5 5l2 2 M17 17l2 2 M19 5l-2 2 M7 17l-2 2",
  search: "M11 4a7 7 0 1 0 .01 0z M20 20l-4-4",
  plus: "M12 5v14 M5 12h14",
  logout: "M9 4H5v16h4 M16 8l4 4-4 4 M20 12H9",
  left: "M14 6l-6 6 6 6",
  right: "M10 6l6 6-6 6",
  menu: "M4 6h16 M4 12h16 M4 18h16",
  mic: "M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3z M5 11a7 7 0 0 0 14 0 M12 18v3",
  clip: "M20 11l-8 8a5 5 0 0 1-7-7l8-8a3.5 3.5 0 0 1 5 5l-8 8a2 2 0 0 1-3-3l7-7",
  camera: "M4 8h4l2-3h4l2 3h4v11H4z M12 11a3 3 0 1 0 .01 0z",
  send: "M4 12l16-8-6 16-3-7z",
  stop: "M7 7h10v10H7z",
  trash: "M5 7h14 M9 7V4h6v3 M7 7l1 13h8l1-13",
  edit: "M4 20h4L19 9l-4-4L4 16z",
  copy: "M8 8h11v12H8z M5 16V4h11",
  speaker: "M4 9h4l5-4v14l-5-4H4z M16 9a4 4 0 0 1 0 6",
  arrow: "M5 12h14 M13 6l6 6-6 6",
  x: "M6 6l12 12 M18 6L6 18",
  sparkle: "M12 3l2 6 6 2-6 2-2 6-2-6-6-2 6-2z",
  research: "M11 4a7 7 0 1 0 .01 0z M20 20l-4-4 M8 11h6",
  brain: "M12 3a6 6 0 0 0-6 6c0 2 1 3 2 4v3h8v-3c1-1 2-2 2-4a6 6 0 0 0-6-6z M9 20h6",
  thumb: "M7 11v9H4v-9z M7 11l4-7c1.6 0 2.6 1.2 2.1 3L12 11h6a2 2 0 0 1 2 2.3l-1 6A2 2 0 0 1 17 21H7",
  refresh: "M20 11a8 8 0 1 0-2 6 M20 4v7h-7",
  history: "M12 7v5l3 2 M4 12a8 8 0 1 0 2.5-5.8 M4 4v4h4",
} as const;
export type IconName = keyof typeof P;

export function Icon({ n, size = 18, className = "" }: { n: IconName; size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden className={`flex-none ${className}`}>
      <path d={P[n]} />
    </svg>
  );
}

export type ChatSummary = { id: string; title: string; updated: number };

function ago(t: number) {
  const m = Math.max(0, Math.round((Date.now() - t) / 60000));
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.round(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.round(h / 24)}d ago`;
}

type Props = {
  collapsed: boolean;
  onToggle: () => void;
  mobileOpen: boolean;
  onClose: () => void;
  name: string;
  email: string;
  chats: ChatSummary[];
  activeId: string;
  query: string;
  setQuery: (q: string) => void;
  searchRef: RefObject<HTMLInputElement | null>;
  onNew: () => void;
  onSelect: (id: string) => void;
  onRename: (id: string) => void;
  onDelete: (id: string) => void;
  onMemory: () => void;
  onSettings: () => void;
};

export default function Sidebar(p: Props) {
  const [busy, setBusy] = useState(false);
  const router = useRouter();
  const c = p.collapsed;

  async function signOut() {
    setBusy(true);
    try { await createClient().auth.signOut(); } catch {}
    window.location.assign("/login");
  }

  const nav = (icon: IconName, label: string, opts: { onClick?: () => void; active?: boolean; badge?: number; soon?: boolean }) => (
    <button
      key={label}
      onClick={opts.onClick}
      disabled={opts.soon}
      title={opts.soon ? `${label} (coming soon)` : label}
      className={`flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm ${FOCUS} ${
        opts.active ? "bg-violet-50 font-medium text-violet-700" : opts.soon ? "cursor-not-allowed text-slate-400" : "text-slate-700 hover:bg-slate-50"
      } ${c ? "justify-center px-0" : ""}`}
    >
      <Icon n={icon} />
      {!c && <span className="flex-1 text-left">{label}</span>}
      {!c && opts.soon && <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-400">soon</span>}
      {!c && opts.badge ? <span className="rounded-full bg-violet-100 px-2 py-0.5 text-xs font-semibold text-violet-700">{opts.badge}</span> : null}
    </button>
  );

  return (
    <>
      {p.mobileOpen && <div className="fixed inset-0 z-40 bg-slate-900/30 md:hidden" onClick={p.onClose} aria-hidden />}
      <aside
        aria-label="Main navigation"
        className={`fixed inset-y-0 left-0 z-50 flex flex-col border-r border-slate-200 bg-white p-3 transition-transform md:static md:z-auto md:translate-x-0 ${
          p.mobileOpen ? "translate-x-0" : "-translate-x-full"
        } ${c ? "w-72 md:w-[4.5rem]" : "w-72"}`}
      >
        <div className={`mb-4 flex items-center ${c ? "justify-center md:flex-col md:gap-3" : "justify-between"}`}>
          <div className="flex items-center gap-2.5">
            <Logo size="small" showText={!c} tagline="Your Personal AI Assistant" />
          </div>
          <button onClick={p.onToggle} aria-label={c ? "Expand sidebar" : "Collapse sidebar"} className={`hidden rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 md:block ${FOCUS}`}>
            <Icon n={c ? "right" : "left"} />
          </button>
          <button onClick={p.onClose} aria-label="Close menu" className={`rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 md:hidden ${FOCUS}`}><Icon n="x" /></button>
        </div>

        <button onClick={() => { p.onNew(); p.onClose(); }} title="New chat"
          className={`mb-3 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-blue-500 py-2.5 text-sm font-semibold text-white shadow-sm shadow-violet-200 hover:brightness-105 ${FOCUS}`}>
          <Icon n="plus" /> {!c && "New Chat"}
        </button>

        {!c && (
          <label className="relative mb-3 block">
            <span className="sr-only">Search chats</span>
            <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"><Icon n="search" size={16} /></span>
            <input ref={p.searchRef} value={p.query} onChange={(e) => p.setQuery(e.target.value)} placeholder="Search chats..."
              className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2 pl-9 pr-3 text-sm outline-none placeholder:text-slate-400 focus:border-violet-400 focus:bg-white" />
          </label>
        )}

        <nav className="space-y-0.5">
          {nav("home", "Home", { active: true, onClick: () => { p.onNew(); p.onClose(); } })}
          {nav("chat", "Chats", { badge: p.chats.length, onClick: () => { p.searchRef.current?.focus(); } })}
          {nav("history", "History", { onClick: () => { router.push("/history"); p.onClose(); } })}
          {nav("image", "Image Studio", { soon: true })}
          {nav("file", "Files & Documents", { soon: true })}
          {nav("tools", "AI Tools", { soon: true })}
          {nav("tasks", "Projects & Tasks", { soon: true })}
          {nav("memory", "Memory", { onClick: () => { p.onMemory(); p.onClose(); } })}
          {nav("settings", "Settings", { onClick: () => { p.onSettings(); p.onClose(); } })}
        </nav>

        {!c && (
          <div className="mt-4 flex min-h-0 flex-1 flex-col border-t border-slate-100 pt-3">
            <div className="mb-1 px-1 text-xs font-semibold text-violet-700">Recent Chats</div>
            <ul className="min-h-0 flex-1 space-y-0.5 overflow-y-auto pr-0.5">
              {p.chats.length === 0 && <li className="px-2 py-2 text-xs text-slate-400">{p.query ? "No chats match your search." : "No chats yet. Start one above."}</li>}
              {p.chats.map((ch) => (
                <li key={ch.id} className={`group flex items-center rounded-xl ${ch.id === p.activeId ? "bg-slate-100" : "hover:bg-slate-50"}`}>
                  <button onClick={() => { p.onSelect(ch.id); p.onClose(); }} className={`min-w-0 flex-1 rounded-xl px-2.5 py-2 text-left ${FOCUS}`}>
                    <div className="truncate text-sm text-slate-800">{ch.title}</div>
                    <div className="text-[11px] text-slate-400">{ago(ch.updated)}</div>
                  </button>
                  <button onClick={() => p.onRename(ch.id)} aria-label={`Rename ${ch.title}`} className={`rounded-md p-1 text-slate-400 opacity-0 hover:text-slate-700 focus-visible:opacity-100 group-hover:opacity-100 ${FOCUS}`}><Icon n="edit" size={14} /></button>
                  <button onClick={() => p.onDelete(ch.id)} aria-label={`Delete ${ch.title}`} className={`mr-1 rounded-md p-1 text-slate-400 opacity-0 hover:text-red-600 focus-visible:opacity-100 group-hover:opacity-100 ${FOCUS}`}><Icon n="trash" size={14} /></button>
                </li>
              ))}
            </ul>
          </div>
        )}
        {c && <div className="flex-1" />}

        <div className={`mt-3 flex items-center gap-2.5 border-t border-slate-100 pt-3 ${c ? "justify-center" : ""}`}>
          <div className="flex h-9 w-9 flex-none items-center justify-center rounded-full bg-gradient-to-br from-violet-600 to-blue-500 text-sm font-semibold text-white" aria-hidden>
            {(p.name || p.email || "K").trim().charAt(0).toUpperCase()}
          </div>
          {!c && (
            <div className="min-w-0 flex-1 leading-tight">
              <div className="truncate text-sm font-medium text-slate-900">{p.name || "Signed in"}</div>
              <div className="truncate text-[11px] text-slate-500">{p.email}</div>
            </div>
          )}
          <button onClick={signOut} disabled={busy} aria-label="Sign out" title="Sign out" className={`rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 disabled:opacity-50 ${FOCUS}`}>
            <Icon n="logout" />
          </button>
        </div>
      </aside>
    </>
  );
}
