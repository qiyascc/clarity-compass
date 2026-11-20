import { useState } from "react";

export function CopyButton({ value, label = "Copy" }: { value: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    await navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <button
      type="button"
      onClick={copy}
      className="shrink-0 rounded-md border border-line bg-white px-2.5 py-1 text-xs font-medium transition-colors hover:border-ink"
    >
      {copied ? "Copied" : label}
    </button>
  );
}

export function CopyField({ value }: { value: string }) {
  return (
    <div className="flex items-center gap-2 rounded-md border border-line bg-paper py-1.5 pr-1.5 pl-3">
      <code className="min-w-0 flex-1 truncate font-mono text-xs">{value}</code>
      <CopyButton value={value} />
    </div>
  );
}
