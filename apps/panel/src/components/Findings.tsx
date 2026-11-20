import { useMemo, useState } from "react";
import { Link } from "react-router";
import type { Finding } from "@/api/client";
import { StatusBadge } from "./StatusBadge";

const CATEGORY_LABELS: Record<string, string> = {
  functional: "Functional",
  accessibility: "Accessibility",
  ux: "UX",
  visual: "Visual",
  content: "Content",
  conversion: "Conversion",
  performance: "Performance",
};

const path = (url: string) => {
  try {
    const parsed = new URL(url);
    return parsed.pathname + parsed.search;
  } catch {
    return url;
  }
};

export function Findings({ runId, findings }: { runId: string; findings: Finding[] }) {
  const [category, setCategory] = useState<string | null>(null);
  const [verifiedOnly, setVerifiedOnly] = useState(false);

  const counts = useMemo(() => {
    const result = new Map<string, number>();
    for (const finding of findings)
      result.set(finding.category, (result.get(finding.category) ?? 0) + 1);
    return result;
  }, [findings]);

  const shown = findings.filter(
    (finding) =>
      (!category || finding.category === category) &&
      (!verifiedOnly || finding.status === "verified"),
  );

  if (findings.length === 0) return <p className="text-sm text-ink-soft">No findings yet.</p>;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Chip active={category === null} onClick={() => setCategory(null)}>
          All {findings.length}
        </Chip>
        {[...counts.entries()].map(([name, count]) => (
          <Chip key={name} active={category === name} onClick={() => setCategory(name)}>
            {CATEGORY_LABELS[name] ?? name} {count}
          </Chip>
        ))}
        <label className="ml-auto flex items-center gap-1.5 text-xs text-ink-soft">
          <input
            type="checkbox"
            className="accent-accent"
            checked={verifiedOnly}
            onChange={(event) => setVerifiedOnly(event.target.checked)}
          />
          Verified only
        </label>
      </div>
      <ul className="divide-y divide-line">
        {shown.map((finding) => (
          <li key={finding.id} className="space-y-1.5 py-3">
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge value={finding.severity} />
              <StatusBadge value={finding.status} />
              <span className="text-xs text-ink-faint">
                {CATEGORY_LABELS[finding.category]} · {finding.viewport} · {path(finding.page_url)}
              </span>
              {finding.page_id && (
                <Link
                  to={`/runs/${runId}/pages/${finding.page_id}?note=${finding.id}`}
                  className="ml-auto text-xs font-medium text-accent hover:underline"
                >
                  Show on page →
                </Link>
              )}
            </div>
            <p className="text-sm font-medium">{finding.title}</p>
            <p className="text-sm text-ink-soft">{finding.description}</p>
            <p className="text-sm">
              <span className="font-medium">Fix: </span>
              {finding.recommendation}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Chip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full px-2.5 py-1 text-xs ${active ? "bg-accent text-white" : "bg-paper text-ink-soft hover:bg-line"}`}
    >
      {children}
    </button>
  );
}
