import { onScopeDispose } from "vue";

const REFRESH_DELAY_MS = 500;

export function useServerEvents(onRefresh: () => void) {
  let source: EventSource | null = null;
  let refreshTimer: number | null = null;
  let hasOpened = false;

  const scheduleRefresh = () => {
    if (refreshTimer != null) return;

    refreshTimer = window.setTimeout(() => {
      refreshTimer = null;
      onRefresh();
    }, REFRESH_DELAY_MS);
  };

  const start = () => {
    if (source != null) return;

    source = new EventSource("/api/events");
    source.addEventListener("refresh", scheduleRefresh);
    source.addEventListener("open", () => {
      if (hasOpened) {
        scheduleRefresh();
      } else {
        hasOpened = true;
      }
    });
  };

  const stop = () => {
    source?.close();
    source = null;
    hasOpened = false;
    if (refreshTimer != null) {
      window.clearTimeout(refreshTimer);
      refreshTimer = null;
    }
  };

  onScopeDispose(stop);

  return { start, stop };
}
