import type { Profile } from "@/api/client";

export type Scope = "site" | "pages" | "single";
export type ViewportName = "desktop" | "tablet" | "mobile";
export type Language = "en" | "tr" | "az" | "ru";

export interface ProfileValues {
  startUrl: string;
  scope: Scope;
  pages: string;
  exclude: string;
  viewports: ViewportName[];
  language: Language;
  maxPages: number;
  maxDepth: number;
  maxActions: number;
}

export const LANGUAGES: Record<Language, string> = {
  en: "English",
  tr: "Türkçe",
  az: "Azərbaycanca",
  ru: "Русский",
};

export const VIEWPORTS: ViewportName[] = ["desktop", "tablet", "mobile"];

export const emptyProfile: ProfileValues = {
  startUrl: "",
  scope: "site",
  pages: "",
  exclude: "",
  viewports: ["desktop", "mobile"],
  language: "en",
  maxPages: 25,
  maxDepth: 3,
  maxActions: 40,
};

const lines = (text: string) =>
  text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

export function toProfile(values: ProfileValues): Profile {
  return {
    start_url: values.startUrl.trim(),
    scope: values.scope,
    pages: values.scope === "pages" ? lines(values.pages) : [],
    exclude_patterns: lines(values.exclude),
    viewports: VIEWPORTS.filter((viewport) => values.viewports.includes(viewport)),
    language: values.language,
    limits: {
      max_pages: values.maxPages,
      max_depth: values.maxDepth,
      max_actions_per_page: values.maxActions,
    },
  };
}

export function fromProfile(profile: Profile): ProfileValues {
  return {
    startUrl: profile.start_url,
    scope: (profile.scope ?? "site") as Scope,
    pages: (profile.pages ?? []).join("\n"),
    exclude: (profile.exclude_patterns ?? []).join("\n"),
    viewports: (profile.viewports ?? emptyProfile.viewports) as ViewportName[],
    language: (profile.language ?? "en") as Language,
    maxPages: profile.limits?.max_pages ?? emptyProfile.maxPages,
    maxDepth: profile.limits?.max_depth ?? emptyProfile.maxDepth,
    maxActions: profile.limits?.max_actions_per_page ?? emptyProfile.maxActions,
  };
}
