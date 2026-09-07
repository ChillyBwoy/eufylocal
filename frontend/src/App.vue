<script setup lang="ts">
import { type MudaComponentVariant } from "@mudakit/ui";
import { MudaErrorBox } from "@mudakit/ui/MudaErrorBox";
import { MudaSpinner } from "@mudakit/ui/MudaSpinner";
import { computed, onMounted, onUnmounted, ref } from "vue";

import { type BleStatus, type MeasurementResponse, type StatusResponse } from "@/api";
import AppHeader from "@/components/AppHeader.vue";
import BluetoothStatusCard from "@/components/BluetoothStatusCard.vue";
import CurrentWeightCard from "@/components/CurrentWeightCard.vue";
import MeasurementHistoryCard from "@/components/MeasurementHistoryCard.vue";

const snapshot = ref<StatusResponse | null>(null);
const measurements = ref<MeasurementResponse[]>([]);
const loading = ref(true);
const refreshError = ref<unknown>(null);
let refreshing = false;
let refreshTimer: number | undefined;

const currentMeasurement = computed(() => snapshot.value?.last_measurement ?? measurements.value[0] ?? null);
const liveWeight = computed(() => {
  const bluetooth = snapshot.value?.bluetooth;
  return bluetooth?.live_weight_active ? bluetooth.live_weight_kg : null;
});
const currentWeight = computed(() => liveWeight.value ?? currentMeasurement.value?.weight_kg ?? null);
const status = computed<BleStatus>(() => snapshot.value?.bluetooth.status ?? "idle");
const statusVariant = computed<MudaComponentVariant>(() => {
  const variants: Record<BleStatus, MudaComponentVariant> = {
    idle: "secondary",
    scanning: "info",
    connecting: "warning",
    connected: "success",
    error: "danger",
  };
  return variants[status.value];
});

async function refresh(): Promise<void> {
  if (refreshing) return;
  refreshing = true;
  try {
    const [statusResponse, measurementsResponse] = await Promise.all([
      fetch("/api/status"),
      fetch("/api/measurements?limit=50"),
    ]);
    if (!statusResponse.ok || !measurementsResponse.ok) {
      throw new Error("The local server returned an error");
    }

    snapshot.value = (await statusResponse.json()) as StatusResponse;
    const payload = (await measurementsResponse.json()) as { measurements: MeasurementResponse[] };
    measurements.value = payload.measurements;
    refreshError.value = null;
  } catch (error) {
    refreshError.value = error;
  } finally {
    loading.value = false;
    refreshing = false;
  }
}

onMounted(() => {
  void refresh();
  refreshTimer = window.setInterval(() => void refresh(), 3_000);
});

onUnmounted(() => window.clearInterval(refreshTimer));
</script>

<template>
  <main class="mx-auto h-full w-full max-w-6xl p-6">
    <AppHeader :status="status" :status-variant="statusVariant" />

    <MudaErrorBox v-if="refreshError && !snapshot" title="Server unreachable" :error="refreshError" />

    <div v-else-if="loading" class="grid min-h-[50vh] place-items-center">
      <MudaSpinner size="large" label="Loading scale data" />
    </div>

    <template v-else>
      <section class="mb-6 grid gap-6 lg:grid-cols-[minmax(0,1.65fr)_minmax(18rem,1fr)]">
        <CurrentWeightCard
          :weight="currentWeight"
          :live-weight="liveWeight"
          :measured-at="currentMeasurement?.measured_at"
        />
        <BluetoothStatusCard :bluetooth="snapshot?.bluetooth" :server-time="snapshot?.server_time" />
      </section>

      <MeasurementHistoryCard :measurements="measurements" />
    </template>
  </main>
</template>
