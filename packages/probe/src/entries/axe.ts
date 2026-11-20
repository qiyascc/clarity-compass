import axe from "axe-core";
import az from "axe-core/locales/az.json";
import ru from "axe-core/locales/ru.json";

const LOCALES: Record<string, axe.Locale> = {
  az: az as unknown as axe.Locale,
  ru: ru as unknown as axe.Locale,
};
const SKIPPED = [
  "color-contrast",
  "image-alt",
  "html-has-lang",
  "target-size",
  "page-has-heading-one",
];

export interface AxeViolation {
  id: string;
  impact: string | null;
  help: string;
  description: string;
  helpUrl: string;
  nodes: { target: string; html: string; summary: string }[];
}

async function run(language: string): Promise<AxeViolation[]> {
  axe.reset();
  const locale = LOCALES[language];
  if (locale) axe.configure({ locale });
  const results = await axe.run(document, {
    runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"] },
    rules: Object.fromEntries(SKIPPED.map((id) => [id, { enabled: false }])),
    resultTypes: ["violations"],
  });
  return results.violations.map((violation) => ({
    id: violation.id,
    impact: violation.impact ?? null,
    help: violation.help,
    description: violation.description,
    helpUrl: violation.helpUrl,
    nodes: violation.nodes.slice(0, 5).map((node) => ({
      target: node.target.map(String).join(" "),
      html: node.html.slice(0, 300),
      summary: node.failureSummary ?? "",
    })),
  }));
}

declare global {
  interface Window {
    __clarityAxe?: { run: typeof run };
  }
}

window.__clarityAxe = { run };
