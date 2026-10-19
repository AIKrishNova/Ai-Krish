"use client";

import Link from "next/link";
import { Suspense, useState, type FormEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import AuthShell, { Heading, linkClass } from "../../components/auth/AuthShell";
import { Alert, Field, MailIcon, PasswordField, SubmitButton } from "../../components/auth/fields";
import { createClient } from "../../lib/supabase/client";
import { isEmail, safeNext } from "../../lib/authValidation";

function LoginForm() {
  const router = useRouter();
  const sp = useSearchParams();
  const [email, setEmail] = useState(sp.get("email") ?? "");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  const [msg, setMsg] = useState("");
  const [state, setState] = useState<"idle" | "loading" | "done">("idle");

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (state !== "idle") return;
    const errs: typeof errors = {};
    if (!isEmail(email)) errs.email = "Enter a valid email address.";
    if (!password) errs.password = "Enter your password.";
    setErrors(errs);
    setMsg("");
    if (errs.email || errs.password) return;
    setState("loading");
    try {
      const { error } = await createClient().auth.signInWithPassword({ email: email.trim(), password });
      if (error) {
        if (error.code === "email_not_confirmed") {
          setState("idle");
          router.push(`/verify?email=${encodeURIComponent(email.trim())}`);
          return;
        }
        setMsg(
          error.code === "invalid_credentials" ? "Incorrect email or password."
          : error.status === 429 ? "Too many attempts. Wait a minute and try again."
          : "We could not sign you in. Try again."
        );
        setState("idle");
        return;
      }
      setState("done");
      router.replace(safeNext(sp.get("next")));
      router.refresh();
    } catch {
      setMsg("Could not reach the server. Check your connection and try again.");
      setState("idle");
    }
  }

  return (
    <>
      <Heading title="Welcome back" subtitle="Sign in to continue to AI KRISH." />
      <form onSubmit={onSubmit} noValidate className="space-y-4">
        {msg && <Alert kind="error">{msg}</Alert>}
        <Field label="Email address" type="email" autoComplete="email" placeholder="you@example.com" icon={<MailIcon />}
          value={email} onChange={(e) => setEmail(e.target.value)} error={errors.email} disabled={state !== "idle"} />
        <PasswordField label="Password" autoComplete="current-password" placeholder="Your password"
          value={password} onChange={(e) => setPassword(e.target.value)} error={errors.password} disabled={state !== "idle"} />
        <div className="flex justify-end text-sm">
          <Link href={`/forgot-password${email ? `?email=${encodeURIComponent(email)}` : ""}`} className={linkClass}>Forgot password?</Link>
        </div>
        <SubmitButton loading={state === "loading"} done={state === "done"}>Sign In</SubmitButton>
      </form>
      <p className="mt-6 text-center text-sm text-slate-600">
        Don&rsquo;t have an account?{" "}
        <Link href={`/signup${email ? `?email=${encodeURIComponent(email)}` : ""}`} className={linkClass}>Create account</Link>
      </p>
    </>
  );
}

export default function LoginPage() {
  return (
    <AuthShell>
      <Suspense fallback={null}><LoginForm /></Suspense>
    </AuthShell>
  );
}
