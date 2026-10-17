"use client";

import Link from "next/link";
import { Suspense, useState, type FormEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import AuthShell, { Heading, linkClass } from "../../components/auth/AuthShell";
import { Alert, Field, MailIcon, PasswordField, SubmitButton, UserIcon } from "../../components/auth/fields";
import { createClient } from "../../lib/supabase/client";
import { isEmail, passwordIssues, passwordScore, STRENGTH_LABELS } from "../../lib/authValidation";

type Errs = { name?: string; email?: string; password?: string; confirm?: string; terms?: string };
const BAR = ["bg-slate-200", "bg-rose-400", "bg-amber-400", "bg-lime-500", "bg-emerald-500"];

function SignupForm() {
  const router = useRouter();
  const sp = useSearchParams();
  const [name, setName] = useState("");
  const [email, setEmail] = useState(sp.get("email") ?? "");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [terms, setTerms] = useState(false);
  const [errors, setErrors] = useState<Errs>({});
  const [msg, setMsg] = useState("");
  const [state, setState] = useState<"idle" | "loading" | "done">("idle");
  const score = passwordScore(password);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (state !== "idle") return;
    const errs: Errs = {};
    if (name.trim().length < 2) errs.name = "Enter your full name.";
    if (!isEmail(email)) errs.email = "Enter a valid email address.";
    const issues = passwordIssues(password);
    if (issues.length) errs.password = issues.join(" ");
    if (confirm !== password) errs.confirm = "Passwords do not match.";
    if (!terms) errs.terms = "Accept the terms and privacy notice to continue.";
    setErrors(errs);
    setMsg("");
    if (Object.keys(errs).length) return;
    setState("loading");
    try {
      const { data, error } = await createClient().auth.signUp({
        email: email.trim(),
        password,
        options: { data: { full_name: name.trim() }, emailRedirectTo: `${window.location.origin}/auth/callback?next=/` },
      });
      if (error) {
        setMsg(
          error.code === "over_email_send_rate_limit" || error.status === 429
            ? "Too many emails were requested. Wait a few minutes and try again."
            : error.code === "weak_password" ? "That password is too weak. Try a longer one."
            : "We could not create the account or send the email. Try again shortly."
        );
        setState("idle");
        return;
      }
      setState("done");
      if (data.session) { router.replace("/"); router.refresh(); return; }
      router.push(`/verify?email=${encodeURIComponent(email.trim())}`);
    } catch {
      setMsg("Could not reach the server. Check your connection and try again.");
      setState("idle");
    }
  }

  const off = state !== "idle";
  return (
    <>
      <Heading title="Create your account" subtitle="Start using AI KRISH in a minute." />
      <form onSubmit={onSubmit} noValidate className="space-y-4">
        {msg && <Alert kind="error">{msg}</Alert>}
        <Field label="Full name" autoComplete="name" placeholder="Your name" icon={<UserIcon />} value={name} onChange={(e) => setName(e.target.value)} error={errors.name} disabled={off} />
        <Field label="Email address" type="email" autoComplete="email" placeholder="you@example.com" icon={<MailIcon />} value={email} onChange={(e) => setEmail(e.target.value)} error={errors.email} disabled={off} />
        <div>
          <PasswordField label="Password" autoComplete="new-password" placeholder="At least 8 characters" value={password} onChange={(e) => setPassword(e.target.value)} error={errors.password} disabled={off} />
          {password && (
            <div className="mt-2" aria-live="polite">
              <div className="flex gap-1" aria-hidden>
                {[1, 2, 3, 4].map((i) => <span key={i} className={`h-1.5 flex-1 rounded-full ${i <= score ? BAR[score] : "bg-slate-200"}`} />)}
              </div>
              <p className="mt-1 text-xs text-slate-600">Strength: {STRENGTH_LABELS[score]}</p>
            </div>
          )}
        </div>
        <PasswordField label="Confirm password" autoComplete="new-password" placeholder="Repeat your password" value={confirm} onChange={(e) => setConfirm(e.target.value)} error={errors.confirm} disabled={off} />
        <div>
          <label className="flex items-start gap-3 text-sm text-slate-700">
            <input type="checkbox" checked={terms} onChange={(e) => setTerms(e.target.checked)} disabled={off}
              className="mt-0.5 h-4 w-4 rounded border-slate-300 accent-violet-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/40" />
            I agree to the terms of use and privacy notice.
          </label>
          {errors.terms && <p role="alert" className="mt-1.5 text-xs text-rose-600">{errors.terms}</p>}
        </div>
        <SubmitButton loading={state === "loading"} done={state === "done"}>Create My Account</SubmitButton>
      </form>
      <p className="mt-6 text-center text-sm text-slate-600">
        Already have an account?{" "}
        <Link href={`/login${email ? `?email=${encodeURIComponent(email)}` : ""}`} className={linkClass}>Sign in</Link>
      </p>
    </>
  );
}

export default function SignupPage() {
  return (
    <AuthShell>
      <Suspense fallback={null}><SignupForm /></Suspense>
    </AuthShell>
  );
}
