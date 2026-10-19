import { fmtBytes, type Limits } from "./limits";

export type ValidImage = { name: string; mime: string; data: Buffer };
export type Skipped = { file: string; reason: string };
export type RawFile = { name: string; type: string; size: number; read: () => Promise<Buffer> };

const HEIC_BRANDS = ["heic", "heix", "hevc", "hevx", "heim", "heis", "mif1", "msf1", "heif"];

// Look at the real bytes, not the file name, so a renamed file cannot sneak through.
export function sniffImage(buf: Uint8Array): string | null {
  if (buf.length < 12) return null;
  const at = (i: number) => buf[i];
  if (at(0) === 0x89 && at(1) === 0x50 && at(2) === 0x4e && at(3) === 0x47) return "image/png";
  if (at(0) === 0xff && at(1) === 0xd8 && at(2) === 0xff) return "image/jpeg";
  const ascii = (s: number, e: number) => String.fromCharCode(...Array.from(buf.slice(s, e)));
  if (ascii(0, 4) === "RIFF" && ascii(8, 12) === "WEBP") return "image/webp";
  if (ascii(4, 8) === "ftyp" && HEIC_BRANDS.includes(ascii(8, 12))) return "image/heic";
  return null;
}

function hint(name: string) {
  const ext = name.split(".").pop()?.toLowerCase() ?? "";
  if (ext === "gif") return " GIF is not supported: save a frame as PNG or JPG.";
  if (["pdf", "doc", "docx", "ppt", "pptx"].includes(ext)) return " Documents are not enabled yet: this version analyses images only.";
  return "";
}

// Checks every file and returns the usable ones plus a clear reason for each file that was skipped.
export async function validateImages(files: RawFile[], limits: Limits): Promise<{ valid: ValidImage[]; skipped: Skipped[] }> {
  const valid: ValidImage[] = [];
  const skipped: Skipped[] = [];
  let total = 0;
  for (const f of files) {
    const name = f.name || "image";
    if (valid.length >= limits.maxFiles) {
      skipped.push({ file: name, reason: `Only ${limits.maxFiles} images can be sent in one message.` });
      continue;
    }
    if (f.size === 0) {
      skipped.push({ file: name, reason: "The file is empty." });
      continue;
    }
    if (f.size > limits.maxFileBytes) {
      skipped.push({ file: name, reason: `Too large (${fmtBytes(f.size)}). The limit is ${fmtBytes(limits.maxFileBytes)} per image.` });
      continue;
    }
    if (total + f.size > limits.maxTotalBytes) {
      skipped.push({ file: name, reason: `Skipped: the images in one message can total at most ${fmtBytes(limits.maxTotalBytes)}.` });
      continue;
    }
    const data = await f.read();
    const mime = sniffImage(data);
    if (!mime) {
      skipped.push({ file: name, reason: `Not a supported image (use JPG, PNG, WEBP or HEIC).${hint(name)}` });
      continue;
    }
    total += data.length;
    valid.push({ name, mime, data });
  }
  return { valid, skipped };
}
