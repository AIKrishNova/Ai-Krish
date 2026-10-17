"use client";

import { Fragment, useState, type ReactNode } from "react";

// A small, safe renderer: builds React elements only (never raw HTML), so model output cannot inject markup.

function inline(s: string, key: string): ReactNode[] {
  return s.split(/(`[^`\n]+`|\*\*[^*\n]+\*\*)/g).map((p, i) => {
    if (p.startsWith("`") && p.endsWith("`") && p.length > 2)
      return <code key={key + i} className="rounded bg-slate-100 px-1 py-0.5 font-mono text-[0.85em] text-violet-700">{p.slice(1, -1)}</code>;
    if (p.startsWith("**") && p.endsWith("**") && p.length > 4)
      return <strong key={key + i} className="font-semibold">{p.slice(2, -2)}</strong>;
    return <Fragment key={key + i}>{p}</Fragment>;
  });
}

function CodeBlock({ code, lang }: { code: string; lang: string }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {}
  }
  return (
    <div className="my-2 overflow-hidden rounded-xl border border-slate-200 bg-slate-50">
      <div className="flex items-center justify-between border-b border-slate-200 bg-white px-3 py-1 text-[11px] text-slate-500">
        <span>{lang || "code"}</span>
        <button onClick={copy} className="rounded px-1.5 py-0.5 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500">
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre className="overflow-x-auto p-3 text-[13px] leading-relaxed text-slate-800"><code>{code.replace(/\n$/, "")}</code></pre>
    </div>
  );
}

function Block({ text, id }: { text: string; id: string }) {
  const out: ReactNode[] = [];
  const lines = text.split("\n");
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const ul = /^\s*[-*•]\s+(.*)$/.exec(line);
    const ol = /^\s*\d+[.)]\s+(.*)$/.exec(line);
    if (ul || ol) {
      const ordered = !!ol;
      const items: string[] = [];
      while (i < lines.length) {
        const m = (ordered ? /^\s*\d+[.)]\s+(.*)$/ : /^\s*[-*•]\s+(.*)$/).exec(lines[i]);
        if (!m) break;
        items.push(m[1]);
        i++;
      }
      const Tag = ordered ? "ol" : "ul";
      out.push(
        <Tag key={id + "l" + i} className={`my-1.5 space-y-0.5 pl-5 ${ordered ? "list-decimal" : "list-disc"} marker:text-slate-400`}>
          {items.map((it, k) => <li key={k}>{inline(it, id + k)}</li>)}
        </Tag>
      );
      continue;
    }
    const h = /^#{1,4}\s+(.*)$/.exec(line);
    if (h) out.push(<div key={id + "h" + i} className="mt-2 font-semibold text-slate-900">{inline(h[1], id + i)}</div>);
    else if (!line.trim()) out.push(<div key={id + "s" + i} className="h-2" />);
    else out.push(<div key={id + "p" + i}>{inline(line, id + i)}</div>);
    i++;
  }
  return <>{out}</>;
}

export default function Markdown({ text }: { text: string }) {
  // split() with two capture groups returns [text, lang, code, text, lang, code, ..., text]
  const parts = text.split(/```([\w+-]*)\n?([\s\S]*?)```/g);
  const nodes: ReactNode[] = [];
  for (let i = 0; i < parts.length; i += 3) {
    if (parts[i]) nodes.push(<Block key={"t" + i} id={"t" + i} text={parts[i]} />);
    if (i + 2 < parts.length) nodes.push(<CodeBlock key={"c" + i} lang={parts[i + 1]} code={parts[i + 2]} />);
  }
  return <div className="space-y-0 break-words text-[15px] leading-relaxed">{nodes}</div>;
}
