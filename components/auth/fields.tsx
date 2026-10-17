"use client";

import { useId, useState, type InputHTMLAttributes, type ReactNode } from "react";

const svg = { width: 18, height: 18, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round" } as const;
export const MailIcon = () => (<svg {...svg}><rect x="3" y="5" width="18" height="14" rx="3" /><path d="m4 8 8 6 8-6" /></svg>);
export const LockIcon = () => (<svg {...svg}><rect x="5" y="11" width="14" height="9" rx="3" /><path d="M8 11V8a4 4 0 0 1 8 0v3" /></svg>);
export const UserIcon = () => (<svg {...svg}><circle cx="12" cy="8" r="4" /><path d="M4.5 20a7.5 7.5 0 0 1 15 0" /></svg>);
const EyeIcon = () => (<svg {...svg}><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z" /><circle cx="12" cy="12" r="3" /></svg>);
const EyeOffIcon = () => (<svg {...svg}><path d="M3 3l18 18M10.6 5.1A9.9 9.9 0 0 1 12 5c6.4 0 10 7 10 7a17 17 0 0 1-3.2 4M6.5 6.6C3.7 8.4 2 12 2 12s3.6 7 10 7c1.6 0 3-.4 4.3-1M9.9 9.9a3 3 0 0 0 4.2 4.2" /></svg>);

type FieldProps = InputHTMLAttributes<HTMLInputElement> & { label: string; icon: ReactNode; error?: string; right?: ReactNode };

export function Field({ label, icon, error, right, ...rest }: FieldProps) {
  const id = useId();
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-slate-800">{label}</label>
      <div className="relative">
        <span aria-hidden className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400">{icon}</span>
        <input
          id={id}
          aria-invalid={!!error}
          aria-describedby={error ? id + "-err" : undefined}
          {...rest}
          className={`w-full rounded-xl border bg-white py-3 pl-11 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus-visible:border-violet-500 focus-visible:ring-2 focus-visible:ring-violet-500/30 disabled:opacity-60 ${right ? "pr-12" : "pr-4"} ${error ? "border-rose-400" : "border-slate-200"}`}
        />
        {right}
      </div>
      {error && <p id={id + "-err"} role="alert" className="mt-1.5 text-xs text-rose-600">{error}</p>}
    </div>
  );
}

export function PasswordField(props: Omit<FieldProps, "icon" | "right" | "type">) {
  const [show, setShow] = useState(false);
  return (
    <Field
      {...props}
      type={show ? "text" : "password"}
      icon={<LockIcon />}
      right={
        <button type="button" onClick={() => setShow((s) => !s)} aria-label={show ? "Hide password" : "Show password"} aria-pressed={show}
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded-lg p-2 text-slate-500 transition hover:text-violet-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/40">
          {show ? <EyeOffIcon /> : <EyeIcon />}
        </button>
      }
    />
  );
}

export function SubmitButton({ loading, done, disabled, children }: { loading?: boolean; done?: boolean; disabled?: boolean; children: ReactNode }) {
  return (
    <button type="submit" disabled={loading || done || disabled}
      className="flex w-full items-center justify-center gap-2 rounded-xl bg-violet-600 px-5 py-3 text-sm font-semibold text-white shadow-[0_8px_20px_-8px_rgba(109,74,255,.7)] transition hover:bg-violet-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60">
      {loading && <span aria-hidden className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white motion-reduce:animate-none" />}
      {done ? "Done" : children}
    </button>
  );
}

export function Alert({ kind, children }: { kind: "error" | "success" | "info"; children: ReactNode }) {
  const tone = kind === "error" ? "border-rose-200 bg-rose-50 text-rose-800" : kind === "success" ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-violet-200 bg-violet-50 text-violet-900";
  return <div role={kind === "error" ? "alert" : "status"} className={`rounded-xl border px-4 py-3 text-sm ${tone}`}>{children}</div>;
}
