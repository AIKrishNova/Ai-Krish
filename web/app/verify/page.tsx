"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import AuthShell, { linkClass } from "../../components/auth/AuthShell";
import { Alert, Field, MailIcon } from "../../components/auth/fields";
import { createClient } from "../../lib/supabase/client";
import { isEmail } from "../../lib/authValidation";

const COPY: Record<string, { title: string; body: string }> = {
  pending: { title: "Check your email", body: "We sent a verification link. Open it in this browser to finish creating your account." },
  verified: { title: "Email verified", body: "Your account is ready. Taking you to AI KRISH." },
  expired: { title: "This link has expired", body: "Verification links work once and expire. Request a new one below." },
  invalid: { title: "This link is not valid", body: "It may have been used already, or opened in a different browser than the one you signed up in. Request a new one below." },
  error: { title: "We could not send the email", body: "Something went wrong while sending. Try again in a moment." },
};
const COOLDOWN = 60;

function VerifyView() {
  const router = useRouter();
  const sp = useSearchParams();
  const raw = sp.get("status") ?? "pending";
  const status = raw in COPY ? raw : "pending";
  const [email, setEmail] = useState(sp.get("email") ?? "");
  const [left, setLeft] = useState(0);
  const [sending, setSending] = useState(false);
  const [note, setNote] = useState<{ kind: "error" | "success"; text: string } | null>(null);

  useEffect(() => {
    if (status !== "verified") return;
    const t = setTimeout(() => router.replace("/"), 2500);
    return () => clearTimeout(t);
  }, [status, router]);

  useEffect(() => {
    if (left <= 0) return;
    const t = setInterval(() => setLeft((n) => Math.max(0, n - 1)), 1000);
    return () => clearInterval(t);
  }, [left > 0]); // eslint-disable-line react-hooks/exhaustive-deps

  async function resend() {
    if (sending || left > 0) return;
    if (!isEmail(email)) { setNote({ kind: "error", text: "Enter the email you signed up with." }); return; }
    setSending(true);
    setNote(null);
    try {
      const { error } = await createClient().auth.resend({
        type: "signup",
        email: email.trim(),
        options: { emailRedirectTo: `${window.location.origin}/auth/callback?next=/` },
      });
      if (error) {
        setNote({ kind: "error", text: error.code === "over_email_send_rate_limit" || error.status === 429 ? "Too many emails were requested. Wait a few minutes and try again." : "We could not send the email. Try again shortly." });
      } else {
        setNote({ kind: "success", text: "A new verification email is on its way." });
        setLeft(COOLDOWN);
      }
    } catch {
      setNote({ kind: "error", text: "Could not reach the server. Check your connection and try again." });
    }
    setSending(false);
  }

  const c = COPY[status];
  return (
    <>
      <h2 className="text-2xl font-semibold tracking-tight">{c.title}</h2>
      <p className="mt-1.5 text-sm text-slate-600">{c.body}</p>
      {status === "pending" && email && <p className="mt-3 break-all rounded-xl bg-violet-50 px-4 py-2.5 text-sm font-medium text-violet-900">{email}</p>}
      {status === "verified" ? (
        <Link href="/" className="mt-6 flex w-full items-center justify-center rounded-xl bg-violet-600 px-5 py-3 text-sm font-semibold text-white hover:bg-violet-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 focus-visible:ring-offset-2">Open AI KRISH</Link>
      ) : (
        <div className="mt-6 space-y-4">
          {note && <Alert kind={note.kind}>{note.text}</Alert>}
          {!sp.get("email") && <Field label="Email address" type="email" autoComplete="email" placeholder="you@example.com" icon={<MailIcon />} value={email} onChange={(e) => setEmail(e.target.value)} />}
          <button type="button" onClick={resend} disabled={sending || left > 0}
            className="w-full rounded-xl border border-violet-200 bg-white px-5 py-3 text-sm font-semibold text-violet-800 transition hover:bg-violet-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/40 disabled:cursor-not-allowed disabled:opacity-60">
            {sending ? "Sending..." : left > 0 ? `Resend available in ${left}s` : "Resend verification email"}
          </button>
          <p className="text-center text-sm text-slate-600"><Link href="/login" className={linkClass}>Back to sign in</Link></p>
        </div>
      )}
    </>
  );
}

export default function VerifyPage() {
  return (
    <AuthShell>
      <Suspense fallback={null}><VerifyView /></Suspense>
    </AuthShell>
  );
}
