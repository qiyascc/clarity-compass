import { mountOverlay, type Overlay, type OverlayData } from "@qiyas/overlay-sdk";
import { type Reply, type Request, viewportFor } from "./shared";

declare global {
  interface Window {
    __clarityExtension?: boolean;
  }
}

async function ask<T>(request: Request): Promise<T> {
  const reply = (await chrome.runtime.sendMessage(request)) as Reply<T>;
  if (!reply.ok) throw new Error(reply.error);
  return reply.value;
}

const loadImage = async (src: string) => {
  const dataUrl = await ask<string>({ type: "image", src });
  return createImageBitmap(await (await fetch(dataUrl)).blob());
};

let overlay: Overlay | null = null;
let shownFor = "";

async function show(): Promise<void> {
  const url = location.href.split("#")[0] ?? location.href;
  if (url === shownFor) return;
  shownFor = url;
  try {
    const data = await ask<OverlayData>({
      type: "overlay",
      url,
      viewport: viewportFor(window.innerWidth),
    });
    if (overlay) overlay.setData(data);
    else overlay = mountOverlay(data, { loadImage });
  } catch (error) {
    overlay?.destroy();
    overlay = null;
    console.info(`Clarity Compass: ${error instanceof Error ? error.message : error}`);
  }
}

if (!window.__clarityExtension) {
  window.__clarityExtension = true;
  void show();
  setInterval(() => void show(), 1_000);
}
