import { Logo } from "@/components/Logo";

export const REPOSITORY = "https://github.com/qiyascc/clarity-compass";

export function Landing() {
  return (
    <div className="flex min-h-screen flex-col bg-white">
      <header className="mx-auto flex h-16 w-full max-w-5xl items-center px-6">
        <Logo />
      </header>
      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col justify-center px-6 pb-24">
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-ink-faint">
          Open source website intelligence
        </p>
        <h1 className="mt-5 max-w-3xl text-5xl font-semibold leading-[1.05] tracking-tighter text-balance sm:text-6xl">
          See your website the way visitors do.
        </h1>
        <p className="mt-6 max-w-xl text-lg leading-relaxed text-ink-soft text-pretty">
          Attention heatmaps, click prediction, an AI design review and a functional audit that
          actually clicks through the site, pinned onto the page itself.
        </p>
        <div className="mt-10">
          <a
            href={REPOSITORY}
            className="inline-flex h-11 items-center gap-2.5 rounded-full bg-ink px-6 text-sm font-medium text-white transition-colors hover:bg-ink/85"
          >
            <svg viewBox="0 0 16 16" className="size-4" fill="currentColor" aria-hidden="true">
              <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
            </svg>
            View on GitHub
          </a>
        </div>
      </main>
      <footer className="mx-auto w-full max-w-5xl px-6 py-8 text-xs text-ink-faint">
        Apache-2.0 with attribution · Qiyas CC
      </footer>
    </div>
  );
}
