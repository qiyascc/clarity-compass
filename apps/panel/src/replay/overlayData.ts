import type { ClickTarget, Note, OverlayData } from "@qiyas/overlay-sdk";
import type { Finding, Page } from "@/api/client";

const artifact = (key: string) => `/api/artifacts/${key}`;

interface CaptureFields {
  final_url: string;
  page_height: number;
}

const VIEWPORTS: Record<string, { width: number; height: number }> = {
  desktop: { width: 1440, height: 900 },
  tablet: { width: 834, height: 1112 },
  mobile: { width: 390, height: 844 },
};

export function viewportOf(page: Page) {
  return VIEWPORTS[page.viewport] ?? (VIEWPORTS.desktop as { width: number; height: number });
}

export function toOverlayData(page: Page, findings: Finding[]): OverlayData {
  const capture = page.capture as unknown as CaptureFields;
  const prediction = page.predictions;
  const clicks: ClickTarget[] = (prediction?.elements ?? [])
    .filter((element) => element.click != null && element.click > 0)
    .map((element) => ({
      index: element.index,
      name: element.name,
      click: element.click ?? 0,
      attention: element.attention,
      anchor: { selector: element.selector, box: element.box },
    }));

  const notes: Note[] = findings
    .filter((finding) => finding.viewport === page.viewport && sameDocument(finding.page_url, page))
    .map((finding) => ({
      id: finding.id ?? `${finding.title}-${finding.page_url}`,
      title: finding.title,
      description: finding.description,
      recommendation: finding.recommendation,
      severity: finding.severity,
      category: finding.category,
      status: finding.status,
      confidence: finding.confidence,
      anchor: finding.anchor ?? null,
    }));

  return {
    url: capture.final_url,
    viewport: viewportOf(page),
    documentHeight: capture.page_height,
    heatmap: prediction
      ? { src: artifact(prediction.heatmap), scale: prediction.heatmap_scale }
      : null,
    clicks,
    notes,
  };
}

function sameDocument(url: string, page: Page): boolean {
  const capture = page.capture as unknown as CaptureFields;
  const strip = (value: string) => value.replace(/[#?].*$/, "").replace(/\/$/, "");
  return strip(url) === strip(page.url) || strip(url) === strip(capture.final_url);
}
