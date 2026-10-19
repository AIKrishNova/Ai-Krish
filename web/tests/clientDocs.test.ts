import { describe, expect, it } from "vitest";
import { DOC_ACCEPT, isImageFile, planDocUpload, splitFiles } from "../lib/clientDocs";

const f = (name: string, size = 1000, type = "") => ({ name, size, type });

describe("splitFiles", () => {
  it("sorts photos and documents by type or extension", () => {
    const r = splitFiles([f("a.png", 1, "image/png"), f("b.PDF"), f("c.heic"), f("d.csv"), f("e.docx")]);
    expect(r.images.map((x) => x.name)).toEqual(["a.png", "c.heic"]);
    expect(r.docs.map((x) => x.name)).toEqual(["b.PDF", "d.csv", "e.docx"]);
    expect(isImageFile({ name: "x.bin", type: "image/webp" })).toBe(true);
  });
  it("offers the document formats the server can read", () => {
    expect(DOC_ACCEPT).toContain(".pdf");
    expect(DOC_ACCEPT).toContain(".docx");
    expect(DOC_ACCEPT).toContain(".csv");
    expect(DOC_ACCEPT).not.toContain("pptx");
  });
});

describe("planDocUpload", () => {
  it("accepts supported documents", () => {
    const r = planDocUpload([f("a.pdf"), f("b.docx"), f("c.csv")], 0);
    expect(r.accept).toEqual([0, 1, 2]);
    expect(r.problems).toEqual([]);
  });
  it("explains each unsupported format", () => {
    const r = planDocUpload([f("old.doc"), f("deck.pptx"), f("sheet.xlsx"), f("pic.xyz"), f("empty.pdf", 0)], 0);
    expect(r.accept).toEqual([]);
    expect(r.problems[0]).toMatch(/\.doc files are not supported/);
    expect(r.problems[1]).toMatch(/PowerPoint.*not supported yet/);
    expect(r.problems[2]).toMatch(/Excel.*CSV/);
    expect(r.problems[3]).toMatch(/unsupported file type/);
    expect(r.problems[4]).toMatch(/empty/);
  });
  it("enforces the size limits", () => {
    const r = planDocUpload([f("big.pdf", 5_000_000)], 0);
    expect(r.problems[0]).toMatch(/too large/);
    const t = planDocUpload([f("a.pdf", 3_000_000), f("b.pdf", 3_000_000)], 0, { maxFiles: 4, maxFileBytes: 4_000_000, maxTotalBytes: 4_000_000, maxRequestBytes: 4_500_000 });
    expect(t.accept).toEqual([0]);
    expect(t.problems[0]).toMatch(/total at most/);
  });
  it("counts documents that are already attached", () => {
    const r = planDocUpload([f("a.pdf"), f("b.pdf")], 2);
    expect(r.accept).toEqual([0]);
    expect(r.problems[0]).toMatch(/At most 3 documents/);
  });
});
