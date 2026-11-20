import { Link, useParams } from "react-router";
import { ApiError, type Finding } from "@/api/client";
import { useFindings, useReport, useRun } from "@/api/hooks";
import { StatusBadge } from "@/components/StatusBadge";
import { Button, Card, ErrorText } from "@/components/ui";
import { formatDate } from "@/format";

const AREAS: Record<string, string> = {
  visual: "Visual design",
  ux: "Usability",
  content: "Content",
  conversion: "Conversion",
  accessibility: "Accessibility",
};

const SEVERITIES = ["critical", "high", "medium", "low", "suggestion"];

const path = (url: string) => {
  try {
    return new URL(url).pathname;
  } catch {
    return url;
  }
};

export function ReportView() {
  const { runId = "" } = useParams();
  const run = useRun(runId);
  const report = useReport(runId);
  const findings = useFindings(runId);

  if (report.error instanceof ApiError && report.error.status === 404) {
    return <p className="text-sm text-ink-soft">The report appears when the analysis finishes.</p>;
  }
  if (!report.data) return <ErrorText error={report.error} />;

  const data = report.data;
  const strengths = data.strengths ?? [];
  const priorities = data.priorities ?? [];
  const byId = new Map((findings.data ?? []).map((finding) => [finding.id, finding]));
  const top = data.top_findings.map((id) => byId.get(id)).filter(Boolean) as Finding[];

  return (
    <article className="space-y-6 print:space-y-4">
      <header className="flex items-end justify-between gap-4">
        <div>
          <Link to={`/runs/${runId}`} className="text-xs text-ink-soft hover:text-ink print:hidden">
            ← Analysis
          </Link>
          <h1 className="text-2xl font-semibold tracking-tight">UX audit report</h1>
          <p className="text-sm text-ink-soft">
            {formatDate(run.data?.finished_at ?? run.data?.created_at)} · {data.totals.pages ?? 0}{" "}
            pages · {data.totals.findings ?? 0} findings ({data.verified} verified, {data.predicted}{" "}
            predicted)
          </p>
        </div>
        <Button onClick={() => window.print()} className="print:hidden">
          Print or save as PDF
        </Button>
      </header>

      {Object.keys(data.scores).length > 0 && (
        <section className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          {Object.entries(AREAS).map(([key, label]) =>
            data.scores[key] === undefined ? null : (
              <div key={key} className="rounded-lg border border-line bg-white p-4">
                <p className="text-xs text-ink-soft">{label}</p>
                <p className="text-3xl font-semibold tabular-nums">{data.scores[key]}</p>
              </div>
            ),
          )}
        </section>
      )}

      {data.assessment && (
        <Card title="Assessment">
          <p className="text-sm leading-relaxed">{data.assessment}</p>
          {strengths.length > 0 && (
            <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-ink-soft">
              {strengths.map((strength) => (
                <li key={strength}>{strength}</li>
              ))}
            </ul>
          )}
        </Card>
      )}

      {priorities.length > 0 && (
        <Card title="What to fix first">
          <ol className="space-y-4">
            {priorities.map((item, index) => (
              <li key={item.title} className="break-inside-avoid">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-xs text-ink-faint">{index + 1}.</span>
                  <span className="font-medium">{item.title}</span>
                  <span className="rounded bg-paper px-1.5 text-xs">impact {item.impact}</span>
                  <span className="rounded bg-paper px-1.5 text-xs">effort {item.effort}</span>
                  {(item.finding_ids ?? []).length > 0 && (
                    <span className="text-xs text-ink-faint">
                      resolves {(item.finding_ids ?? []).length} finding
                      {(item.finding_ids ?? []).length > 1 ? "s" : ""}
                    </span>
                  )}
                </div>
                <p className="mt-1 text-sm text-ink-soft">{item.why}</p>
                <p className="text-sm">{item.action}</p>
              </li>
            ))}
          </ol>
        </Card>
      )}

      <Card title="Findings by severity">
        <div className="flex flex-wrap gap-4 text-sm">
          {SEVERITIES.map((severity) => (
            <span key={severity} className="flex items-center gap-2">
              <StatusBadge value={severity} />
              <span className="tabular-nums">{data.by_severity[severity] ?? 0}</span>
            </span>
          ))}
        </div>
      </Card>

      {top.length > 0 && (
        <Card title="Most serious findings">
          <ul className="divide-y divide-line">
            {top.map((finding) => (
              <li key={finding.id} className="break-inside-avoid py-3">
                <div className="flex flex-wrap items-center gap-2">
                  <StatusBadge value={finding.severity} />
                  <StatusBadge value={finding.status} />
                  <span className="text-xs text-ink-faint">
                    {path(finding.page_url)} · {finding.viewport}
                  </span>
                </div>
                <p className="mt-1 text-sm font-medium">{finding.title}</p>
                <p className="text-sm text-ink-soft">{finding.description}</p>
                <p className="text-sm">
                  <span className="font-medium">Fix: </span>
                  {finding.recommendation}
                </p>
              </li>
            ))}
          </ul>
        </Card>
      )}

      <Card title="Pages">
        <table className="w-full text-left text-sm">
          <thead className="text-xs text-ink-faint">
            <tr>
              <th className="py-1.5 font-normal">Page</th>
              <th className="py-1.5 font-normal">Type</th>
              <th className="py-1.5 text-right font-normal">Findings</th>
              <th className="py-1.5 text-right font-normal">Critical</th>
              <th className="py-1.5 text-right font-normal">UX score</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {data.pages.map((page) => (
              <tr key={page.url}>
                <td className="py-2 font-mono text-xs">{path(page.url)}</td>
                <td className="py-2 capitalize">{page.kind?.replace("_", " ") ?? "-"}</td>
                <td className="py-2 text-right tabular-nums">{page.findings}</td>
                <td className="py-2 text-right tabular-nums">{page.critical}</td>
                <td className="py-2 text-right tabular-nums">{page.scores?.ux ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </article>
  );
}
