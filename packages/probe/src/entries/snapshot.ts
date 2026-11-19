import { takeSnapshot } from "../snapshot";

declare global {
  interface Window {
    __claritySnapshot?: { version: string; take: typeof takeSnapshot };
  }
}

window.__claritySnapshot = { version: "1", take: takeSnapshot };
