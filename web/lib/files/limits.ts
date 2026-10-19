// Shared by the browser and the server. The server can override these with env vars.
export const IMAGE_MIME = ["image/png", "image/jpeg", "image/webp", "image/heic", "image/heif"] as const;

export type Limits = {
  maxFiles: number;
  maxFileBytes: number;
  maxTotalBytes: number;
  maxRequestBytes: number;
};

// Vercel serverless functions reject request bodies above about 4.5 MB, so the defaults stay below that.
export const DEFAULT_LIMITS: Limits = {
  maxFiles: 4,
  maxFileBytes: 4_000_000,
  maxTotalBytes: 4_000_000,
  maxRequestBytes: 4_500_000,
};

function num(v: string | undefined, fallback: number) {
  const n = Number(v);
  return Number.isFinite(n) && n > 0 ? n : fallback;
}

export function serverLimits(env: Record<string, string | undefined> = process.env): Limits {
  return {
    maxFiles: num(env.MAX_IMAGES_PER_MESSAGE, DEFAULT_LIMITS.maxFiles),
    maxFileBytes: num(env.MAX_IMAGE_BYTES, DEFAULT_LIMITS.maxFileBytes),
    maxTotalBytes: num(env.MAX_UPLOAD_BYTES, DEFAULT_LIMITS.maxTotalBytes),
    maxRequestBytes: num(env.MAX_REQUEST_BYTES, DEFAULT_LIMITS.maxRequestBytes),
  };
}

export function fmtBytes(n: number) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}
