export function formatWeight(value: number | null): string {
  return value === null ? "--" : value.toFixed(2);
}

export function formatDateTime(value: string, format: "datetime" | "date" | "time"): string {
  const date = new Date(value);

  switch (format) {
    case "date":
      return new Intl.DateTimeFormat(undefined, { dateStyle: "short" }).format(date);
    case "datetime":
      return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date);
    case "time":
      return new Intl.DateTimeFormat(undefined, { timeStyle: "short", hour12: false }).format(date);
  }
}
