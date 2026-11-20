export interface Settings {
  apiBase: string;
  key: string;
}

export interface SitePage {
  id: string;
  url: string;
  final_url: string;
  viewport: string;
}

export interface SiteInfo {
  name: string;
  start_url: string;
  run_id: string | null;
  pages: SitePage[];
}

export type Request =
  | { type: "overlay"; url: string; viewport: string }
  | { type: "image"; src: string };

export type Reply<T> = { ok: true; value: T } | { ok: false; error: string };

export function normaliseApiBase(input: string): string {
  const trimmed = input.trim().replace(/\/+$/, "");
  const withScheme = /^https?:\/\//.test(trimmed) ? trimmed : `https://${trimmed}`;
  return new URL(withScheme).origin;
}

export function siteOrigins(site: SiteInfo): string[] {
  const hosts = new Set<string>();
  for (const url of [site.start_url, ...site.pages.flatMap((page) => [page.url, page.final_url])]) {
    try {
      const { protocol, host } = new URL(url);
      const bare = host.replace(/^www\./, "");
      hosts.add(`${protocol}//${bare}`);
      hosts.add(`${protocol}//www.${bare}`);
    } catch {
      // ignore malformed URLs from the server
    }
  }
  return [...hosts].sort();
}

export function belongsToSite(url: string, origins: string[]): boolean {
  try {
    return origins.includes(new URL(url).origin);
  } catch {
    return false;
  }
}

export function viewportFor(width: number): "desktop" | "tablet" | "mobile" {
  if (width < 600) return "mobile";
  if (width < 1000) return "tablet";
  return "desktop";
}
