import { onScopeDispose, ref } from "vue";

import type { MeasurementUnit } from "@/api";

const REFRESH_DELAY_MS = 500;

export interface ServerSideStatusMessage {
  type: "status";
  weight: number;
  impedance_ohm: number | null;
  unit: MeasurementUnit;
}

type ServerSideMessage = { type: "ready" } | { type: "refresh" } | ServerSideStatusMessage;

export function useServerEvents(onStatus: (message: ServerSideStatusMessage) => void, onRefresh: () => Promise<void>) {
  const source = ref<EventSource | null>(null);
  const refreshTimer = ref<number | null>(null);
  const hasOpened = ref(false);

  const scheduleRefresh = () => {
    if (refreshTimer.value != null) {
      return;
    }

    refreshTimer.value = window.setTimeout(() => {
      refreshTimer.value = null;
      onRefresh();
    }, REFRESH_DELAY_MS);
  };

  const handleMessage = (event: MessageEvent<string>) => {
    const message = JSON.parse(event.data) as ServerSideMessage;
    if (message.type === "status") {
      onStatus(message);
    } else if (message.type === "refresh") {
      scheduleRefresh();
    }
  };

  const handleOpen = () => {
    if (hasOpened.value) {
      scheduleRefresh();
    } else {
      hasOpened.value = true;
    }
  };

  const start = () => {
    if (source.value != null) return;

    source.value = new EventSource("/api/sse/");
    source.value.addEventListener("message", handleMessage);
    source.value.addEventListener("open", handleOpen);
  };

  const stop = () => {
    source.value?.removeEventListener("open", handleOpen);
    source.value?.removeEventListener("message", handleMessage);
    source.value?.close();
    source.value = null;
    hasOpened.value = false;

    if (refreshTimer.value != null) {
      window.clearTimeout(refreshTimer.value);
      refreshTimer.value = null;
    }
  };

  onScopeDispose(stop);

  return { start, stop };
}
