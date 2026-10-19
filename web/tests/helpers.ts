export const PNG = Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), Buffer.alloc(40)]);
export const JPEG = Buffer.concat([Buffer.from([0xff, 0xd8, 0xff, 0xe0]), Buffer.alloc(40)]);
export const WEBP = Buffer.concat([Buffer.from("RIFF"), Buffer.alloc(4), Buffer.from("WEBP"), Buffer.alloc(20)]);
export const HEIC = Buffer.concat([Buffer.alloc(4), Buffer.from("ftypheic"), Buffer.alloc(20)]);
export const PDF = Buffer.from("%PDF-1.4\n1 0 obj\n<<>>\nendobj\n");

export function raw(name: string, data: Buffer, type = "") {
  return { name, type, size: data.length, read: async () => data };
}

export function formWith(files: { name: string; data: Buffer; type?: string }[], fields: Record<string, string> = {}) {
  const f = new FormData();
  for (const x of files) f.append("files", new File([new Uint8Array(x.data)], x.name, { type: x.type ?? "" }));
  for (const [k, v] of Object.entries(fields)) f.append(k, v);
  return f;
}
