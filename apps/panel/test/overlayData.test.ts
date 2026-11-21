import { describe, expect, it } from "vitest";
import type { Finding, Page } from "@/api/client";
import { toOverlayData } from "@/replay/overlayData";

const page = {
  id: "p1",
  url: "https://example.com/",
  viewport: "mobile",
  status_code: 200,
  title: "Home",
  capture: { final_url: "https://qiyas.cc/", page_height: 4200 },
  predictions: {
    sections: [],
    heatmap: "run/home/mobile/attention.png",
    heatmap_scale: 0.923,
    agreement: 0.8,
    models: [],
    elements: [
      {
        index: 3,
        selector: "#cta",
        tag: "a",
        name: "Contact",
        box: { x: 10, y: 20, width: 100, height: 40 },
        interactive: true,
        section: 0,
        attention: 0.05,
        attention_density: 3,
        click: 0.4,
      },
      {
        index: 4,
        selector: "h1",
        tag: "h1",
        name: "Welcome",
        box: { x: 0, y: 0, width: 300, height: 60 },
        interactive: false,
        section: 0,
        attention: 0.2,
        attention_density: 2,
        click: null,
      },
    ],
  },
} as unknown as Page;

const finding = (overrides: Partial<Finding>): Finding =>
  ({
    id: "f1",
    page_url: "https://qiyas.cc/",
    viewport: "mobile",
    category: "ux",
    severity: "high",
    status: "predicted",
    confidence: 0.7,
    title: "Weak CTA",
    description: "d",
    recommendation: "r",
    anchor: { selector: "#cta" },
    evidence: [],
    source: "test",
    ...overrides,
  }) as Finding;

describe("toOverlayData", () => {
  it("maps predictions to heatmap and click targets", () => {
    const data = toOverlayData(page, []);
    expect(data.url).toBe("https://qiyas.cc/");
    expect(data.viewport).toEqual({ width: 390, height: 844 });
    expect(data.heatmap).toEqual({
      src: "/api/artifacts/run/home/mobile/attention.png",
      scale: 0.923,
    });
    expect(data.clicks?.map((click) => click.name)).toEqual(["Contact"]);
  });

  it("keeps only findings for this page and viewport", () => {
    const data = toOverlayData(page, [
      finding({}),
      finding({ id: "f2", viewport: "desktop" }),
      finding({ id: "f3", page_url: "https://qiyas.cc/about/" }),
      finding({ id: "f4", page_url: "https://example.com/#top" }),
    ]);
    expect(data.notes?.map((note) => note.id)).toEqual(["f1", "f4"]);
  });
});
