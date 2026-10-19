// Browser-side helpers for document attachments: sorting files into photos and documents,
// and checking documents before they are uploaded. The server checks everything again.
import { DEFAULT_LIMITS } from "./files/limits";

export type DocItem = {
  id: string;
  name: string;
  kind: "pdf" | "docx" | "csv" | "text";
  chars: number;
  pages?: number;
  truncated: boolean;
  text: string;
};

export const DOC_EXT = ["pdf", "docx", "csv", "tsv", "txt", "md", "markdown", "json", "log", "xml", "yaml", "yml"];
export const DOC_ACCEPT = DOC_EXT.map((e) => "." + e).join(",");
export const MAX_DOCS = 3;
const IMAGE_EXT = ["png", "jpg", "jpeg", "webp", "heic", "heif", "gif", "bmp", "tif", "tiff", "avif"];

const ext = (name: string) => (name.split(".").pop() || "").toLowerCase();

export function isImageFile(f: { name: string; type: string }) {
  return f.type.startsWith("image/") || IMAGE_EXT.includes(ext(f.name));
}

export function splitFiles<T extends { name: string; type: string }>(files: T[]): { images: T[]; docs: T[] } {
  const images: T[] = [];
  const docs: T[] = [];
  for (const f of files) (isImageFile(f) ? images : docs).push(f);
  return { images, docs };
}

const mb = (n: number) => (n / 1_000_000).toFixed(1);

export function planDocUpload(
  files: { name: string; size: number }[],
  existingCount: number,
  limits = DEFAULT_LIMITS,
  maxDocs = MAX_DOCS
): { accept: number[]; problems: string[] } {
  const accept: number[] = [];
  const problems: string[] = [];
  let total = 0;
  files.forEach((f, i) => {
    const e = ext(f.name);
    if (existingCount + accept.length >= maxDocs) {
      problems.push(`${f.name}: skipped. At most ${maxDocs} documents can be attached to one message.`);
    } else if (e === "doc") {
      problems.push(`${f.name}: old .doc files are not supported. Save it as .docx and try again.`);
    } else if (e === "ppt" || e === "pptx") {
      problems.push(`${f.name}: PowerPoint files are not supported yet. Use PDF, Word (.docx), CSV or a text file.`);
    } else if (e === "xls" || e === "xlsx") {
      problems.push(`${f.name}: Excel files are not supported yet. Save the sheet as CSV and attach that.`);
    } else if (!DOC_EXT.includes(e)) {
      problems.push(`${f.name}: unsupported file type. Use PDF, Word (.docx), CSV or a text file.`);
    } else if (f.size === 0) {
      problems.push(`${f.name}: the file is empty.`);
    } else if (f.size > limits.maxFileBytes) {
      problems.push(`${f.name}: too large (${mb(f.size)} MB). The limit is ${mb(limits.maxFileBytes)} MB per document.`);
    } else if (total + f.size > limits.maxTotalBytes) {
      problems.push(`${f.name}: skipped. Documents added together can total at most ${mb(limits.maxTotalBytes)} MB.`);
    } else {
      total += f.size;
      accept.push(i);
    }
  });
  return { accept, problems };
}
