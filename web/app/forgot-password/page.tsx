"use client";

import Link from "next/link";
import { Suspense, useState, type FormEvent } from "react";
import { useSearchParams } from "next/navigation";
import AuthShell, { Heading, linkClass } from "../../components/auth/AuthShell";
import { Alert, Field, MailIcon, SubmitButton } from "../../components/auth/fields";
import { createClient } from "../../lib/supabase/client";
import { isEmail } from "../../lib/authValidation";

function ForgotForm() {
  const sp = useSearchParams();
  const [email, setEmail] = useState(sp.get("email") ?? "");
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const linkProblem = sp.get("status");

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (loading) return;
    setMsg("");
    if (!isEmail(email)) { setError("Enter a valid email address."); return; }
    setError("");
    setLoading(true);
    try {
      const { error: err } = await createClient().auth.resetPasswordForEmail(email.trim(), {
        redirectTo: `${window.location.origin}/auth/callback?next=/reset-password`,
      });
      // Same message whether or not the account exists, so this form cannot be used to find accounts.
      if (err && (err.status === 429 || err.code === "over_email_send_rate_limit")) setMsg("Too many emails were requested. Wait a few minutes and try again.");
      else setSent(true);
    } catch {
      setMsg("Could not reach the server. Check your connection and try again.");
    }
    setLoading(false);
  }

  return (
    <>
      <Heading title="Reset your password" subtitle="Enter your email and we will send you a reset link." />
      {sent ? (
        <Alert kind="success">If an account exists for that email, a reset link is on its way. The link expires and works once.</Alert>
      ) : (
        <form onSubmit={onSubmit} noValidate className="space-y-4">
          {linkProblem && <Alert kind="info">That reset link has expired or was already used. Request a new one.</Alert>}
          {msg && <Alert kind="error">{msg}</Alert>}
          <Field label="Email address" type="email" autoComplete="email" placeholder="you@example.com" icon={<MailIcon />} value={email} onChange={(e) => setEmail(e.target.value)} error={error} disabled={loading} />
          <SubmitButton loading={loading}>Send Reset Link</SubmitButton>
        </form>
      )}
      <p className="mt-6 text-center text-sm text-slate-600"><Link href="/login" className={linkClass}>Back to sign in</Link></p>
    </>
  );
}

export default function ForgotPasswordPage() {
  return (
    <AuthShell>
      <Suspense fallback={null}><ForgotForm /></Suspense>
    </AuthShell>
  );
}
