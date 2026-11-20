const styles: Record<string, string> = {
  queued: "bg-paper text-ink-soft",
  running: "bg-accent-soft text-accent",
  completed: "bg-emerald-50 text-emerald-700",
  failed: "bg-red-50 text-critical",
  cancelled: "bg-paper text-ink-faint",
  critical: "bg-red-50 text-critical",
  high: "bg-orange-50 text-high",
  medium: "bg-amber-50 text-medium",
  low: "bg-blue-50 text-low",
  suggestion: "bg-indigo-50 text-suggestion",
  verified: "bg-emerald-50 text-emerald-700",
  predicted: "bg-paper text-ink-soft",
};

export function StatusBadge({ value }: { value: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium capitalize ${styles[value] ?? styles.queued}`}
    >
      {value === "running" && <span className="size-1.5 animate-pulse rounded-full bg-accent" />}
      {value}
    </span>
  );
}
