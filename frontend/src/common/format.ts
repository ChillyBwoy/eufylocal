export function formatWeight(value: number | null): string {
  return value === null ? "--" : value.toFixed(2);
}

export function formatTime(value: string | null | undefined): string {
  return value != null
    ? new Intl.DateTimeFormat(undefined, { timeStyle: "short" }).format(new Date(value))
    : "No measurement yet";
}

export function formatDateTime(value: string | null | undefined): string {
  return value != null
    ? new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value))
    : "No measurement yet";
}
