"use client";

import { useState } from "react";
import { createClient } from "../lib/supabase/client";

export default function LogoutButton() {
  const [busy, setBusy] = useState(false);
  async function out() {
    setBusy(true);
    try { await createClient().auth.signOut(); } catch {}
    window.location.assign("/login");
  }
  return (
    <button onClick={out} disabled={busy}
      className="fixed bottom-4 left-4 z-30 rounded-full border border-slate-300 bg-white/90 px-4 py-1.5 text-xs font-medium text-slate-700 shadow-sm backdrop-blur hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 disabled:opacity-60">
      {busy ? "Signing out..." : "Sign out"}
    </button>
  );
}
