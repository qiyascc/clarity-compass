export function Logo({
  className = "",
  compact = false,
}: {
  className?: string;
  compact?: boolean;
}) {
  return (
    <span
      className={`inline-flex items-center gap-2 whitespace-nowrap font-semibold tracking-tight ${className}`}
    >
      <svg viewBox="0 0 24 24" className="size-5" aria-hidden="true">
        <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2" />
        <path d="M15.5 8.5 13.2 13.2 8.5 15.5l2.3-4.7z" fill="currentColor" />
      </svg>
      <span className={compact ? "max-sm:sr-only" : ""}>Clarity Compass</span>
    </span>
  );
}
