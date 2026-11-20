const styles: Record<string, string> = {
  queued: "border border-line text-ink-faint",
  running: "border border-ink text-ink",
  completed: "bg-ink text-white",
  failed: "border border-dashed border-ink text-ink",
  cancelled: "border border-line text-ink-faint line-through",
  critical: "bg-ink text-white",
  high: "border border-ink text-ink",
  medium: "border border-ink-faint text-ink",
  low: "border border-line text-ink-soft",
  suggestion: "border border-dashed border-line text-ink-faint",
  verified: "bg-ink text-white",
  predicted: "border border-line text-ink-soft",
};

export function StatusBadge({ value }: { value: string }) {
  return (
    <span
      className={`inline-flex h-5 items-center gap-1.5 rounded-full px-2 text-[11px] font-medium capitalize tracking-wide ${styles[value] ?? styles.queued}`}
    >
      {value === "running" && <span className="size-1.5 animate-pulse rounded-full bg-ink" />}
      {value}
    </span>
  );
}
