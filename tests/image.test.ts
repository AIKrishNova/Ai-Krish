import { describe, expect, it } from "vitest";
import { sniffImage, validateImages } from "../lib/files/image";
import { DEFAULT_LIMITS } from "../lib/files/limits";
import { HEIC, JPEG, PDF, PNG, WEBP, raw } from "./helpers";

describe("sniffImage", () => {
  it("recognises PNG, JPEG, WEBP and HEIC by their real bytes", () => {
    expect(sniffImage(PNG)).toBe("image/png");
    expect(sniffImage(JPEG)).toBe("image/jpeg");
    expect(sniffImage(WEBP)).toBe("image/webp");
    expect(sniffImage(HEIC)).toBe("image/heic");
  });
  it("rejects non-images and tiny buffers", () => {
    expect(sniffImage(PDF)).toBeNull();
    expect(sniffImage(Buffer.from("hello"))).toBeNull();
  });
});

describe("validateImages", () => {
  it("accepts real images even when the file name is wrong", async () => {
    const r = await validateImages([raw("photo.txt", PNG)], DEFAULT_LIMITS);
    expect(r.valid).toHaveLength(1);
    expect(r.valid[0].mime).toBe("image/png");
    expect(r.skipped).toHaveLength(0);
  });
  it("skips a renamed PDF with a clear reason", async () => {
    const r = await validateImages([raw("fake.jpg", PDF)], DEFAULT_LIMITS);
    expect(r.valid).toHaveLength(0);
    expect(r.skipped[0].reason).toMatch(/Not a supported image/);
  });
  it("explains that GIFs and documents are not supported yet", async () => {
    const r = await validateImages([raw("a.gif", Buffer.from("GIF89a" + "x".repeat(30))), raw("report.pdf", PDF)], DEFAULT_LIMITS);
    expect(r.skipped[0].reason).toMatch(/GIF/);
    expect(r.skipped[1].reason).toMatch(/images only/);
  });
  it("rejects empty files and oversized files without reading them", async () => {
    let read = false;
    const big = { name: "big.png", type: "", size: DEFAULT_LIMITS.maxFileBytes + 1, read: async () => { read = true; return PNG; } };
    const r = await validateImages([raw("empty.png", Buffer.alloc(0)), big], DEFAULT_LIMITS);
    expect(r.skipped[0].reason).toMatch(/empty/i);
    expect(r.skipped[1].reason).toMatch(/Too large/);
    expect(read).toBe(false);
  });
  it("enforces the per-message count and total size", async () => {
    const files = Array.from({ length: 6 }, (_, i) => raw(`p${i}.png`, PNG));
    const r = await validateImages(files, { ...DEFAULT_LIMITS, maxFiles: 4 });
    expect(r.valid).toHaveLength(4);
    expect(r.skipped).toHaveLength(2);
    const t = await validateImages([raw("a.png", PNG), raw("b.png", PNG)], { ...DEFAULT_LIMITS, maxTotalBytes: PNG.length + 5 });
    expect(t.valid).toHaveLength(1);
    expect(t.skipped[0].reason).toMatch(/total/);
  });
});
