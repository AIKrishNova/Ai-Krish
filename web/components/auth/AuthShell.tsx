import type { ReactNode } from "react";
import Logo from "../Logo";


const ic = { width: 20, height: 20, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round" } as const;
const FEATURES: { text: string; icon: ReactNode }[] = [
  { text: "Intelligent AI conversations", icon: <svg {...ic}><path d="M4 5h16v11H9l-5 4V5Z" /></svg> },
  { text: "Create images and analyze documents", icon: <svg {...ic}><rect x="4" y="4" width="16" height="16" rx="3" /><circle cx="9" cy="9" r="1.5" /><path d="m4 17 5-5 4 4 3-3 4 4" /></svg> },
  { text: "Voice assistance and productivity tools", icon: <svg {...ic}><rect x="9" y="3" width="6" height="11" rx="3" /><path d="M5 11a7 7 0 0 0 14 0M12 18v3" /></svg> },
];

export default function AuthShell({ children }: { children: ReactNode }) {
  return (
    <div className="relative min-h-screen overflow-hidden bg-white text-slate-900">
      <div aria-hidden className="pointer-events-none absolute -left-40 -top-40 h-[26rem] w-[26rem] rounded-full bg-violet-100/70 blur-3xl" />
      <div aria-hidden className="pointer-events-none absolute -bottom-48 right-0 h-[22rem] w-[22rem] rounded-full bg-sky-100/60 blur-3xl" />
      <div className="relative mx-auto grid min-h-screen w-full max-w-6xl items-center gap-8 px-5 py-8 sm:px-8 lg:grid-cols-2 lg:gap-16">
        <aside className="flex flex-col gap-8 lg:min-h-[34rem] lg:justify-between">
          <div className="flex justify-center lg:hidden"><Logo size="medium" /></div>
          <div>
            <h1 className="text-center text-2xl font-semibold leading-tight tracking-tight sm:text-3xl lg:max-w-md lg:text-left lg:text-5xl lg:leading-[1.08]">
              Your AI. Your Ideas. Unlimited Possibilities.
            </h1>
            <p className="mt-4 hidden max-w-md text-base leading-relaxed text-slate-600 sm:block">
              Meet your personal AI assistant for conversations, creativity, coding, research, and productivity.
            </p>
          </div>
          <div className="hidden justify-center lg:flex"><Logo size="large" /></div>
          <ul className="hidden gap-3 lg:grid">
            {FEATURES.map((f) => (
              <li key={f.text} className="flex items-center gap-3 text-sm text-slate-700">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-50 text-violet-700">{f.icon}</span>
                {f.text}
              </li>
            ))}
          </ul>
          <p className="hidden text-xs text-slate-500 lg:block">Intelligence meets creativity.</p>
        </aside>
        <main className="w-full">
          <div className="mx-auto w-full max-w-md rounded-3xl border border-slate-200 bg-white p-6 shadow-[0_24px_60px_-30px_rgba(76,29,149,.25)] sm:p-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

export function Heading({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="mb-6">
      <h2 className="text-2xl font-semibold tracking-tight">{title}</h2>
      <p className="mt-1.5 text-sm text-slate-600">{subtitle}</p>
    </div>
  );
}

export const linkClass = "font-medium text-violet-700 underline-offset-4 hover:underline focus-visible:rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/40";
