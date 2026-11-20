const dateTime = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" });

export const formatDate = (value: string | null | undefined) =>
  value ? dateTime.format(new Date(value)) : "-";

export function formatDuration(from: string | null | undefined, to: string | null | undefined) {
  if (!from) return "-";
  const seconds = Math.max(
    0,
    Math.round(((to ? Date.parse(to) : Date.now()) - Date.parse(from)) / 1000),
  );
  return seconds < 60 ? `${seconds}s` : `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
}
