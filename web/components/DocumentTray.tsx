"use client";

import type { DocItem } from "../lib/clientDocs";

const LABEL: Record<DocItem["kind"], string> = { pdf: "PDF", docx: "DOC", csv: "CSV", text: "TXT" };

export default function DocumentTray({
  items,
  loading,
  progress,
  onRemove,
}: {
  items: DocItem[];
  loading: boolean;
  progress: number | null;
  onRemove: (id: string) => void;
}) {
  if (items.length === 0 && !loading) return null;
  return (
    <div className="mb-2 flex flex-wrap gap-2">
      {items.map((d) => (
        <div key={d.id} className="relative flex max-w-[16rem] items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 py-1.5 pl-2 pr-7">
          <span className="flex h-9 w-9 flex-none items-center justify-center rounded-lg bg-violet-100 text-[10px] font-bold text-violet-700">{LABEL[d.kind]}</span>
          <div className="min-w-0">
            <div className="truncate text-xs text-slate-700" title={d.name}>{d.name}</div>
            <div className="text-[10px] text-slate-400">
              {d.pages ? `${d.pages} page${d.pages === 1 ? "" : "s"} · ` : ""}
              {d.chars.toLocaleString("en-US")} characters{d.truncated ? " (shortened)" : ""}
            </div>
          </div>
          <button
            onClick={() => onRemove(d.id)}
            aria-label={`Remove ${d.name}`}
            className="absolute right-1.5 top-1.5 flex h-5 w-5 items-center justify-center rounded-full text-xs leading-none text-slate-500 hover:bg-slate-200"
          >
            x
          </button>
        </div>
      ))}
      {loading && (
        <div role="progressbar" aria-label="Reading documents" aria-valuenow={progress ?? undefined} aria-valuemin={0} aria-valuemax={100}
          className="flex animate-pulse items-center rounded-xl border border-dashed border-slate-300 px-3 py-2 text-xs text-slate-500">
          Reading documents{progress !== null && progress < 100 ? ` (uploading ${progress}%)` : "..."}
        </div>
      )}
    </div>
  );
}
