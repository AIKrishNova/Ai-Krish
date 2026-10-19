// Browser-only helpers. Photos are shrunk before upload so they fit the 4 MB request limit and upload quickly.
import { IMAGE_MIME, fmtBytes } from "./files/limits";

export const CLIENT_MAX_RAW_BYTES = 25_000_000;

export type PrepareResult = { file: File } | { error: string };

export async function prepareImage(file: File, maxEdge = 2000, maxBytes = 4_000_000): Promise<PrepareResult> {
  if (file.size === 0) return { error: `${file.name}: the file is empty.` };
  if (file.size > CLIENT_MAX_RAW_BYTES) return { error: `${file.name}: too large (${fmtBytes(file.size)}). Choose a photo under ${fmtBytes(CLIENT_MAX_RAW_BYTES)}.` };
  const looksImage = file.type.startsWith("image/") || /\.(png|jpe?g|webp|heic|heif)$/i.test(file.name);
  if (!looksImage) {
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (ext && ["pdf", "doc", "docx", "ppt", "pptx"].includes(ext)) return { error: `${file.name}: documents are not supported yet. This version reads images only.` };
    return { error: `${file.name}: not an image. Use JPG, PNG, WEBP or HEIC.` };
  }
  if (file.type === "image/gif") return { error: `${file.name}: GIF is not supported. Save a frame as PNG or JPG.` };

  try {
    const bmp = await createImageBitmap(file);
    const scale = Math.min(1, maxEdge / Math.max(bmp.width, bmp.height));
    const w = Math.max(1, Math.round(bmp.width * scale));
    const h = Math.max(1, Math.round(bmp.height * scale));
    const canvas = document.createElement("canvas");
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("no canvas");
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, w, h);
    ctx.drawImage(bmp, 0, 0, w, h);
    bmp.close?.();
    const blob: Blob | null = await new Promise((res) => canvas.toBlob(res, "image/jpeg", 0.88));
    if (!blob) throw new Error("encode failed");
    const originalOk = (IMAGE_MIME as readonly string[]).includes(file.type) && file.size <= maxBytes && file.size <= blob.size;
    if (originalOk) return { file };
    if (blob.size > maxBytes) return { error: `${file.name}: still ${fmtBytes(blob.size)} after shrinking. Choose a smaller photo.` };
    return { file: new File([blob], file.name.replace(/\.[^.]+$/, "") + ".jpg", { type: "image/jpeg" }) };
  } catch {
    // The browser could not decode it (for example HEIC in Chrome). Send it as is if it is small enough; the server checks it again.
    if (file.size <= maxBytes) return { file };
    return { error: `${file.name}: this browser cannot shrink this photo and it is larger than ${fmtBytes(maxBytes)}. Try a JPG or PNG.` };
  }
}
