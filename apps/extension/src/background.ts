import { belongsToSite, type Reply, type Request, type Settings } from "./shared";

interface Stored {
  settings?: Settings;
  origins?: string[];
}

async function stored(): Promise<Stored> {
  return (await chrome.storage.local.get(["settings", "origins"])) as Stored;
}

async function call(path: string): Promise<Response> {
  const { settings } = await stored();
  if (!settings) throw new Error("The extension is not connected yet.");
  const response = await fetch(`${settings.apiBase}${path}`, {
    headers: { Authorization: `Bearer ${settings.key}` },
  });
  if (response.status === 401)
    throw new Error("The key was rejected. Generate a new one in the panel.");
  if (!response.ok) throw new Error(`Clarity Compass answered ${response.status}.`);
  return response;
}

async function handle(request: Request): Promise<unknown> {
  if (request.type === "overlay") {
    const query = new URLSearchParams({ url: request.url, viewport: request.viewport });
    return (await call(`/api/extension/overlay?${query}`)).json();
  }
  const blob = await (await call(request.src)).blob();
  const buffer = new Uint8Array(await blob.arrayBuffer());
  let binary = "";
  for (const byte of buffer) binary += String.fromCharCode(byte);
  return `data:${blob.type || "image/png"};base64,${btoa(binary)}`;
}

chrome.runtime.onMessage.addListener((request: Request, _sender, respond) => {
  handle(request)
    .then((value) => respond({ ok: true, value } satisfies Reply<unknown>))
    .catch((error: unknown) =>
      respond({ ok: false, error: error instanceof Error ? error.message : String(error) }),
    );
  return true;
});

chrome.tabs.onUpdated.addListener(async (tabId, change, tab) => {
  if (change.status !== "complete" || !tab.url) return;
  const { origins = [] } = await stored();
  if (!belongsToSite(tab.url, origins)) return;
  if (!(await chrome.permissions.contains({ origins: [`${new URL(tab.url).origin}/*`] }))) return;
  await chrome.scripting.executeScript({ target: { tabId }, files: ["content.js"] });
});
