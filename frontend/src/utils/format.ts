export function formatWeight(value: number | null): string {
  return value === null ? "--" : value.toFixed(2);
}

export function formatTime(value: string | null | undefined): string {
  if (!value) return "No measurement yet";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "medium",
  }).format(new Date(value));
}
