import type { ReactNode } from "react";
import { Link } from "react-router";
import { CopyField } from "@/components/CopyButton";

export const EXTENSION_DOWNLOAD = "/downloads/clarity-compass-extension.zip";

function Step({ number, title, children }: { number: number; title: string; children: ReactNode }) {
  return (
    <li className="grid grid-cols-[2rem_1fr] gap-4 border-t border-line py-6 first:border-t-0">
      <span className="grid size-8 place-items-center rounded-full border border-ink font-mono text-xs">
        {number}
      </span>
      <div className="min-w-0 space-y-3">
        <h2 className="font-semibold tracking-tight">{title}</h2>
        <div className="space-y-3 text-sm leading-relaxed text-ink-soft">{children}</div>
      </div>
    </li>
  );
}

export function ExtensionGuide() {
  const panel = window.location.host;

  return (
    <article className="mx-auto max-w-2xl">
      <header className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight">Browser extension</h1>
        <p className="mt-2 text-sm leading-relaxed text-ink-soft">
          The extension draws the analysis on the real site while you browse it: the attention
          heatmap, predicted clicks and numbered review notes. It works in Chrome, Edge and Brave on
          a computer; mobile browsers do not run extensions.
        </p>
      </header>

      <ol className="rounded-xl border border-line bg-white px-6">
        <Step number={1} title="Download the extension">
          <p>Unzip it into a folder you will keep; Chrome loads it from there.</p>
          <a
            href={EXTENSION_DOWNLOAD}
            download
            className="inline-flex h-9 items-center rounded-md bg-ink px-3.5 text-sm font-medium text-white transition-colors hover:bg-ink/85"
          >
            Download .zip
          </a>
        </Step>

        <Step number={2} title="Open the extensions page">
          <p>Browsers do not open this address from a link, so paste it into the address bar.</p>
          <CopyField value="chrome://extensions" />
          <p>In Edge it is edge://extensions, in Brave brave://extensions.</p>
        </Step>

        <Step number={3} title="Load it">
          <p>
            Turn on <strong className="text-ink">Developer mode</strong> in the top right corner,
            choose <strong className="text-ink">Load unpacked</strong> and pick the unzipped folder.
            Pin Clarity Compass from the puzzle icon in the toolbar so it is one click away.
          </p>
        </Step>

        <Step number={4} title="Create a key for the site">
          <p>
            Open the site in{" "}
            <Link to="/" className="font-medium text-ink underline underline-offset-4">
              Sites
            </Link>{" "}
            and press <strong className="text-ink">Generate key</strong> under Extension key. The
            key is shown once; copy it right away.
          </p>
        </Step>

        <Step number={5} title="Connect the extension">
          <p>Click the extension icon and fill in both fields:</p>
          <div className="space-y-2">
            <p className="text-xs font-medium text-ink">Panel address</p>
            <CopyField value={panel} />
            <p className="text-xs font-medium text-ink">Site key</p>
            <p>The key from the previous step.</p>
          </div>
          <p>Allow access to the site when the browser asks.</p>
        </Step>

        <Step number={6} title="Open the site">
          <p>
            Browse the audited site as usual. Analysed pages show the overlay; the small panel in
            the corner toggles the heatmap, clicks and notes and steps through the notes.
          </p>
        </Step>
      </ol>
    </article>
  );
}
