import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
} from "react";

type Tone = "primary" | "plain" | "danger";

const tones: Record<Tone, string> = {
  primary: "bg-ink text-white hover:bg-ink/85 disabled:bg-ink/40",
  plain: "border border-line bg-white text-ink hover:border-ink disabled:text-ink-faint",
  danger: "border border-ink bg-white text-ink hover:bg-ink hover:text-white",
};

export function Button({
  tone = "plain",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { tone?: Tone }) {
  return (
    <button
      type="button"
      className={`inline-flex h-9 shrink-0 items-center gap-2 whitespace-nowrap rounded-md px-3.5 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink disabled:cursor-not-allowed ${tones[tone]} ${className}`}
      {...props}
    />
  );
}

export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    // biome-ignore lint/a11y/noLabelWithoutControl: the control is passed in as children
    <label className="block space-y-1.5">
      <span className="text-sm font-medium text-ink">{label}</span>
      {children}
      {hint && <span className="block text-xs text-ink-faint">{hint}</span>}
    </label>
  );
}

const control =
  "w-full rounded-md border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition focus:border-ink focus:ring-2 focus:ring-ink/10";

export const Input = (props: InputHTMLAttributes<HTMLInputElement>) => (
  <input className={control} {...props} />
);

export const TextArea = (props: InputHTMLAttributes<HTMLTextAreaElement> & { rows?: number }) => (
  <textarea className={`${control} font-mono text-xs`} {...props} />
);

export const Select = (props: SelectHTMLAttributes<HTMLSelectElement>) => (
  <select className={control} {...props} />
);

export function Card({
  title,
  actions,
  children,
}: {
  title?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="rounded-xl border border-line bg-white">
      {(title || actions) && (
        <header className="flex items-center justify-between border-b border-line px-5 py-3">
          <h2 className="text-sm font-semibold tracking-tight">{title}</h2>
          {actions}
        </header>
      )}
      <div className="p-5">{children}</div>
    </section>
  );
}

export function ErrorText({ error }: { error: unknown }) {
  if (!error) return null;
  const message = error instanceof Error ? error.message : String(error);
  return (
    <p className="whitespace-pre-line border-l-2 border-ink pl-3 text-sm font-medium text-ink">
      {message}
    </p>
  );
}
