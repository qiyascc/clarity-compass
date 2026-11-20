import { normaliseApiBase, type Settings, type SiteInfo, siteOrigins } from "./shared";

const form = document.getElementById("connect") as HTMLFormElement;
const api = document.getElementById("api") as HTMLInputElement;
const key = document.getElementById("key") as HTMLInputElement;
const open = document.getElementById("open") as HTMLButtonElement;
const status = document.getElementById("status") as HTMLParagraphElement;
let site: SiteInfo | null = null;

function say(text: string, error = false) {
  status.textContent = text;
  status.classList.toggle("error", error);
}

async function fetchSite(apiBase: string, siteKey: string): Promise<SiteInfo> {
  const response = await fetch(`${apiBase}/api/extension/site`, {
    headers: { Authorization: `Bearer ${siteKey}` },
  });
  if (response.status === 401) throw new Error("This key is not valid.");
  if (!response.ok) throw new Error(`The panel answered ${response.status}.`);
  return (await response.json()) as SiteInfo;
}

function ready(info: SiteInfo) {
  site = info;
  open.hidden = false;
  say(
    info.run_id
      ? `${info.name}: ${info.pages.length} analysed page views.`
      : `${info.name} has no finished analysis yet.`,
  );
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const apiBase = normaliseApiBase(api.value);
    if (!(await chrome.permissions.request({ origins: [`${apiBase}/*`] }))) {
      say("Access to the panel address is needed to load the analysis.", true);
      return;
    }
    say("Checking the key…");
    const info = await fetchSite(apiBase, key.value.trim());
    await chrome.storage.local.set({
      settings: { apiBase, key: key.value.trim() },
      origins: siteOrigins(info),
    });
    ready(info);
  } catch (error) {
    say(error instanceof Error ? error.message : String(error), true);
  }
});

open.addEventListener("click", async () => {
  if (!site) return;
  const origins = siteOrigins(site).map((origin) => `${origin}/*`);
  if (!(await chrome.permissions.request({ origins }))) {
    say("Access to the site is needed to draw the overlay on it.", true);
    return;
  }
  await chrome.tabs.create({ url: site.start_url });
  window.close();
});

chrome.storage.local.get("settings").then(async (items) => {
  const { settings } = items as { settings?: Settings };
  if (!settings) return;
  api.value = settings.apiBase;
  key.value = settings.key;
  try {
    ready(await fetchSite(settings.apiBase, settings.key));
  } catch (error) {
    say(error instanceof Error ? error.message : String(error), true);
  }
});
