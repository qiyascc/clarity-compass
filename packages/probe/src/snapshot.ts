import { snapshot } from "rrweb-snapshot";

export interface PageSnapshot {
  version: 1;
  url: string;
  title: string;
  viewport: { width: number; height: number };
  documentHeight: number;
  capturedAt: string;
  tree: NonNullable<ReturnType<typeof snapshot>>;
}

export function takeSnapshot(): PageSnapshot {
  const tree = snapshot(document, {
    inlineStylesheet: true,
    maskAllInputs: true,
    recordCanvas: false,
    blockClass: "clarity-block",
    slimDOM: { script: true, comment: true, headFavicon: true, headMetaVerification: true },
  });
  if (!tree) throw new Error("document could not be serialised");
  return {
    version: 1,
    url: location.href,
    title: document.title,
    viewport: { width: window.innerWidth, height: window.innerHeight },
    documentHeight: Math.max(
      document.documentElement.scrollHeight,
      document.body?.scrollHeight ?? 0,
    ),
    capturedAt: new Date().toISOString(),
    tree,
  };
}
