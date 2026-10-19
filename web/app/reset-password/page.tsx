"use client";

import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import AuthShell, { Heading, linkClass } from "../../components/auth/AuthShell";
import { Alert, PasswordField, SubmitButton } from "../../components/auth/fields";
import { createClient } from "../../lib/supabase/client";
import { passwordIssues } from "../../lib/authValidation";

export default function ResetPasswordPage() {
  const router = useRouter();
  const [ready, setReady] = useState<boolean | null>(null);
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [errors, setErrors] = useState<{ password?: string; confirm?: string }>({});
  const [msg, setMsg] = useState("");
  const [state, setState] = useState<"idle" | "loading" | "done">("idle");

  useEffect(() => {
    createClient().auth.getUser().then(({ data }) => setReady(!!data.user)).catch(() => setReady(false));
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (state !== "idle") return;
    const errs: typeof errors = {};
    const issues = passwordIssues(password);
    if (issues.length) errs.password = issues.join(" ");
    if (confirm !== password) errs.confirm = "Passwords do not match.";
    setErrors(errs);
    setMsg("");
    if (errs.password || errs.confirm) return;
    setState("loading");
    try {
      const { error } = await createClient().auth.updateUser({ password });
      if (error) {
        setMsg(error.code === "same_password" ? "Choose a password you have not used before." : "We could not update the password. Request a new reset link and try again.");
        setState("idle");
        return;
      }
      setState("done");
      setTimeout(() => { router.replace("/"); router.refresh(); }, 1500);
    } catch {
      setMsg("Could not reach the server. Check your connection and try again.");
      setState("idle");
    }
  }

  return (
    <AuthShell>
      <Heading title="Choose a new password" subtitle="Pick something you have not used on other sites." />
      {ready === null ? (
        <p className="text-sm text-slate-600" role="status">Checking your reset link...</p>
      ) : !ready ? (
        <Alert kind="error">This reset link is invalid or has expired. <Link href="/forgot-password" className={linkClass}>Request a new one</Link>.</Alert>
      ) : state === "done" ? (
        <Alert kind="success">Password updated. Taking you to AI KRISH.</Alert>
      ) : (
        <form onSubmit={onSubmit} noValidate className="space-y-4">
          {msg && <Alert kind="error">{msg}</Alert>}
          <PasswordField label="New password" autoComplete="new-password" placeholder="At least 8 characters" value={password} onChange={(e) => setPassword(e.target.value)} error={errors.password} disabled={state !== "idle"} />
          <PasswordField label="Confirm new password" autoComplete="new-password" placeholder="Repeat the password" value={confirm} onChange={(e) => setConfirm(e.target.value)} error={errors.confirm} disabled={state !== "idle"} />
          <SubmitButton loading={state === "loading"}>Update Password</SubmitButton>
        </form>
      )}
      <p className="mt-6 text-center text-sm text-slate-600"><Link href="/login" className={linkClass}>Back to sign in</Link></p>
    </AuthShell>
  );
}
