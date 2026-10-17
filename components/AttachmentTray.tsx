"use client";

import { fmtBytes } from "../lib/files/limits";

export type Attachment = { id: string; file: File; previewUrl: string };

export default function AttachmentTray({
  items,
  preparing,
  progress,
  onRemove,
}: {
  items: Attachment[];
  preparing: number;
  progress: number | null;
  onRemove: (id: string) => void;
}) {
  if (items.length === 0 && preparing === 0) return null;
  return (
    <div className="mt-3">
      <div className="flex flex-wrap gap-2">
        {items.map((a) => (
          <div key={a.id} className="relative flex w-40 items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 p-1.5">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={a.previewUrl} alt={`Preview of ${a.file.name}`} className="h-12 w-12 flex-none rounded-lg object-cover" />
            <div className="min-w-0 flex-1">
              <div className="truncate text-xs text-slate-700">{a.file.name}</div>
              <div className="text-[10px] text-slate-400">{fmtBytes(a.file.size)}</div>
            </div>
            <button
              onClick={() => onRemove(a.id)}
              disabled={progress !== null}
              aria-label={`Remove ${a.file.name}`}
              className="absolute -right-1.5 -top-1.5 flex h-5 w-5 items-center justify-center rounded-full border border-slate-300 bg-white text-xs leading-none text-slate-600 hover:bg-slate-100 disabled:opacity-40"
            >
              x
            </button>
          </div>
        ))}
        {preparing > 0 && (
          <div className="flex h-15 w-40 animate-pulse items-center justify-center rounded-xl border border-dashed border-slate-300 text-xs text-slate-500">
            Preparing {preparing} photo{preparing === 1 ? "" : "s"}...
          </div>
        )}
      </div>
      {progress !== null && (
        <div className="mt-2" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
          <div className="h-1.5 overflow-hidden rounded-full bg-slate-200">
            <div className="h-full bg-blue-600 transition-all" style={{ width: `${progress}%` }} />
          </div>
          <div className="mt-1 text-[11px] text-slate-500">{progress < 100 ? `Uploading ${progress}%` : "Upload complete"}</div>
        </div>
      )}
    </div>
  );
}
