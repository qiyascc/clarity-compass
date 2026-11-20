import { useMemo, useState } from "react";
import { Link, useParams } from "react-router";
import type { Page } from "@/api/client";
import { isActive, useCancelRun, useFindings, usePages, useRun } from "@/api/hooks";
import { HeatImage } from "@/components/HeatImage";
import { StatusBadge } from "@/components/StatusBadge";
import { Button, Card, ErrorText } from "@/components/ui";
import { formatDate, formatDuration } from "@/format";

interface Capture {
  final_url: string;
  load_ms: number;
  page_height: number;
  sections: { index: number; scroll_y: number; height: number; screenshot: string }[];
  console: { level: string; text: string }[];
  page_errors: string[];
  request_issues: { url: string; status: number | null; error: string | null }[];
  blocked_requests: { url: string; method: string }[];
}

const artifact = (key: string) => `/api/artifacts/${key}`;

export function RunDetail() {
  const { runId = "" } = useParams();
  const run = useRun(runId);
  const live = isActive(run.data);
  const pages = usePages(runId, live);
  const findings = useFindings(runId);
  const cancel = useCancelRun(runId);

  const byUrl = useMemo(() => {
    const groups = new Map<string, Page[]>();
    for (const page of pages.data ?? []) {
      groups.set(page.url, [...(groups.get(page.url) ?? []), page]);
    }
    return [...groups.entries()];
  }, [pages.data]);

  if (!run.data) return <ErrorText error={run.error} />;
  const failures = (run.data.progress.failures as string[] | undefined) ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <Link to={`/sites/${run.data.site_id}`} className="text-xs text-ink-soft hover:text-ink">
            ← Site
          </Link>
          <h1 className="flex items-center gap-3 text-xl font-semibold tracking-tight">
            Analysis <StatusBadge value={run.data.status} />
          </h1>
          <p className="text-sm text-ink-soft">
            Started {formatDate(run.data.started_at ?? run.data.created_at)} ·{" "}
            {formatDuration(run.data.started_at, run.data.finished_at)}
            {run.data.stage && live && ` · ${run.data.stage}`}
          </p>
        </div>
        {live && (
          <Button tone="danger" onClick={() => cancel.mutate()} disabled={cancel.isPending}>
            Cancel
          </Button>
        )}
      </div>

      {run.data.error && (
        <div className="rounded-md border border-critical/30 bg-red-50 p-4 font-mono text-xs text-critical">
          {run.data.error}
        </div>
      )}
      {failures.length > 0 && (
        <Card title={`${failures.length} pages could not be captured`}>
          <ul className="space-y-1 font-mono text-xs text-ink-soft">
            {failures.map((failure) => (
              <li key={failure}>{failure}</li>
            ))}
          </ul>
        </Card>
      )}

      <Card title={`Findings${findings.data ? ` (${findings.data.length})` : ""}`}>
        {findings.data?.length === 0 ? (
          <p className="text-sm text-ink-soft">No findings yet.</p>
        ) : (
          <ul className="divide-y divide-line">
            {findings.data?.map((finding) => (
              <li key={finding.id} className="space-y-1 py-3">
                <div className="flex items-center gap-2">
                  <StatusBadge value={finding.severity} />
                  <StatusBadge value={finding.status} />
                  <span className="text-sm font-medium">{finding.title}</span>
                </div>
                <p className="text-sm text-ink-soft">{finding.description}</p>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <div className="space-y-4">
        <h2 className="text-sm font-semibold">Pages ({byUrl.length})</h2>
        {byUrl.map(([url, captures]) => (
          <PageCard key={url} url={url} captures={captures} />
        ))}
      </div>
    </div>
  );
}

function PageCard({ url, captures }: { url: string; captures: Page[] }) {
  const [selected, setSelected] = useState(0);
  const [showHeat, setShowHeat] = useState(true);
  const page = captures[selected] ?? captures[0];
  if (!page) return null;
  const capture = page.capture as unknown as Capture;
  const prediction = page.predictions;
  const attentionKey = (index: number) => {
    const key = prediction?.sections.find((section) => section.index === index)?.combined;
    return key ? artifact(key) : undefined;
  };
  const topClicks = [...(prediction?.elements ?? [])]
    .filter((element) => element.click != null)
    .sort((a, b) => (b.click ?? 0) - (a.click ?? 0))
    .slice(0, 5);
  const errors =
    capture.console.filter((entry) => entry.level === "error").length + capture.page_errors.length;

  return (
    <Card
      title={page.title || url}
      actions={
        <div className="flex items-center gap-1">
          {prediction && (
            <label className="mr-3 flex items-center gap-1.5 text-xs text-ink-soft">
              <input
                type="checkbox"
                className="accent-accent"
                checked={showHeat}
                onChange={(event) => setShowHeat(event.target.checked)}
              />
              Attention
            </label>
          )}
          {captures.map((item, index) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setSelected(index)}
              className={`rounded px-2 py-1 text-xs capitalize ${index === selected ? "bg-accent-soft text-accent" : "text-ink-soft hover:bg-paper"}`}
            >
              {item.viewport}
            </button>
          ))}
        </div>
      }
    >
      <p className="mb-3 truncate font-mono text-xs text-ink-soft">{capture.final_url}</p>
      <dl className="mb-4 flex flex-wrap gap-x-6 gap-y-1 text-xs text-ink-soft">
        <Stat label="Status" value={page.status_code ?? "-"} />
        <Stat label="Load" value={`${capture.load_ms} ms`} />
        <Stat label="Height" value={`${capture.page_height}px`} />
        <Stat label="Sections" value={capture.sections.length} />
        <Stat label="JS errors" value={errors} warn={errors > 0} />
        <Stat
          label="Failed requests"
          value={capture.request_issues.length}
          warn={capture.request_issues.length > 0}
        />
        <Stat label="Blocked" value={capture.blocked_requests.length} />
        {prediction && <Stat label="Model agreement" value={prediction.agreement.toFixed(2)} />}
      </dl>
      <div className="flex gap-3 overflow-x-auto pb-2">
        {capture.sections.map((section) => (
          <a
            key={section.index}
            href={artifact(section.screenshot)}
            target="_blank"
            rel="noreferrer"
            className="shrink-0"
          >
            <HeatImage
              screenshot={artifact(section.screenshot)}
              attention={attentionKey(section.index)}
              showHeat={showHeat}
              className={page.viewport === "desktop" ? "h-40" : "h-56"}
            />
          </a>
        ))}
      </div>
      {topClicks.length > 0 && (
        <div className="mt-4">
          <h3 className="mb-2 text-xs font-semibold tracking-wide text-ink-faint uppercase">
            Predicted clicks
          </h3>
          <ol className="space-y-1 text-sm">
            {topClicks.map((element) => (
              <li key={element.index} className="flex items-center gap-3">
                <span className="w-12 text-right font-mono text-xs">
                  {Math.round((element.click ?? 0) * 100)}%
                </span>
                <span className="truncate">{element.name || element.selector}</span>
                <span className="ml-auto shrink-0 text-xs text-ink-faint">
                  attention {(element.attention * 100).toFixed(1)}%
                </span>
              </li>
            ))}
          </ol>
        </div>
      )}
    </Card>
  );
}

function Stat({ label, value, warn }: { label: string; value: string | number; warn?: boolean }) {
  return (
    <div>
      <dt className="inline">{label} </dt>
      <dd className={`inline font-medium ${warn ? "text-critical" : "text-ink"}`}>{value}</dd>
    </div>
  );
}
