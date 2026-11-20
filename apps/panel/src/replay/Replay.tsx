import { mountOverlay, type Overlay } from "@qiyascc/clarity-overlay";
import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { createCache, createMirror, rebuildIntoSandboxedIframe } from "rrweb-snapshot";
import { api, type Page } from "@/api/client";
import { useFindings, usePages } from "@/api/hooks";
import { ErrorText } from "@/components/ui";
import { toOverlayData, viewportOf } from "./overlayData";

interface Snapshot {
  tree: Parameters<typeof rebuildIntoSandboxedIframe>[0];
}

const loadImage = async (src: string) => {
  const response = await fetch(src, { credentials: "same-origin" });
  if (!response.ok) throw new Error(`heatmap request failed with ${response.status}`);
  return createImageBitmap(await response.blob());
};

const strip = (url: string) => url.replace(/[#?].*$/, "").replace(/\/$/, "");
const finalUrl = (page: Page) => (page.capture as { final_url: string }).final_url;

export function Replay() {
  const { runId = "", pageId = "" } = useParams();
  const navigate = useNavigate();
  const pages = usePages(runId, false);
  const findings = useFindings(runId);
  const stage = useRef<HTMLDivElement>(null);
  const host = useRef<HTMLDivElement>(null);
  const frame = useRef<HTMLIFrameElement | null>(null);
  const overlay = useRef<Overlay | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [scale, setScale] = useState(1);
  const scaleRef = useRef(scale);
  scaleRef.current = scale;

  const page = pages.data?.find((item) => item.id === pageId);
  const siblings = useMemo(
    () => pages.data?.filter((item) => page && item.url === page.url) ?? [],
    [pages.data, page],
  );
  const viewport = page ? viewportOf(page) : { width: 1440, height: 900 };

  useEffect(() => {
    const element = stage.current;
    if (!element) return;
    const resize = () => setScale(Math.min(1, (element.clientWidth - 32) / viewport.width));
    resize();
    const observer = new ResizeObserver(resize);
    observer.observe(element);
    return () => observer.disconnect();
  }, [viewport.width, page?.id]);

  useEffect(() => {
    if (frame.current) frame.current.style.transform = `scale(${scale})`;
  }, [scale]);

  useEffect(() => {
    const root = host.current;
    const snapshotKey = (page?.capture as { snapshot?: string } | undefined)?.snapshot;
    if (!root || !page || !snapshotKey || !findings.data || !pages.data) return;
    let cancelled = false;
    const all = pages.data;
    const notes = findings.data;
    const { width, height } = viewportOf(page);

    const openLink = (event: MouseEvent) => {
      const link = (event.target as Element).closest?.("a[href]") as HTMLAnchorElement | null;
      if (!link) return;
      event.preventDefault();
      const wanted = strip(link.href);
      const target = all.find(
        (item) =>
          item.viewport === page.viewport &&
          (strip(item.url) === wanted || strip(finalUrl(item)) === wanted),
      );
      if (target) navigate(`/runs/${runId}/pages/${target.id}`);
    };

    api<Snapshot>(`/artifacts/${snapshotKey}`)
      .then((snapshot) => {
        if (cancelled) return;
        root.replaceChildren();
        const { iframe } = rebuildIntoSandboxedIframe(snapshot.tree, {
          root,
          iframeAttributes: {
            title: "Page replay",
            style: `width:${width}px;height:${height}px;border:0;transform-origin:0 0;transform:scale(${scaleRef.current})`,
          },
          cache: createCache(),
          mirror: createMirror(),
          hackCss: true,
        });
        frame.current = iframe;
        const doc = iframe.contentDocument;
        if (!doc) return;
        doc.addEventListener("click", openLink);
        overlay.current = mountOverlay(toOverlayData(page, notes), { document: doc, loadImage });
      })
      .catch((reason: unknown) => {
        if (!cancelled) setError(reason);
      });

    return () => {
      cancelled = true;
      overlay.current?.destroy();
      overlay.current = null;
      frame.current = null;
      root.replaceChildren();
    };
  }, [page, pages.data, findings.data, navigate, runId]);

  if (pages.isPending) return null;
  if (!page) return <ErrorText error={pages.error ?? "Page not found"} />;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <Link to={`/runs/${runId}`} className="text-xs text-ink-soft hover:text-ink">
            ← Analysis
          </Link>
          <h1 className="truncate text-lg font-semibold tracking-tight">
            {page.title || page.url}
          </h1>
          <p className="truncate font-mono text-xs text-ink-soft">{page.url}</p>
        </div>
        <div className="flex gap-1">
          {siblings.map((item) => (
            <Link
              key={item.id}
              to={`/runs/${runId}/pages/${item.id}`}
              className={`rounded px-2.5 py-1 text-xs capitalize ${item.id === page.id ? "bg-accent-soft text-accent" : "text-ink-soft hover:bg-white"}`}
            >
              {item.viewport}
            </Link>
          ))}
        </div>
      </div>
      <ErrorText error={error} />
      <div ref={stage} className="rounded-lg border border-line bg-white p-4">
        <div
          className="mx-auto overflow-hidden rounded border border-line"
          style={{ width: viewport.width * scale, height: viewport.height * scale }}
        >
          <div ref={host} key={page.id} />
        </div>
      </div>
    </div>
  );
}
