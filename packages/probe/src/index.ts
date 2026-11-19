import { collect } from "./collect";

declare global {
  interface Window {
    __clarityProbe?: { version: string; collect: typeof collect };
  }
}

window.__clarityProbe = { version: "1", collect };
