<script setup lang="ts">
import { MudaCard } from "@mudakit/ui/MudaCard";
import { MudaErrorBox } from "@mudakit/ui/MudaErrorBox";
import { MudaSpinner } from "@mudakit/ui/MudaSpinner";
import { MudaTable, MudaTableCell, MudaTableHead, MudaTableRow } from "@mudakit/ui/MudaTable";
import { MudaTag } from "@mudakit/ui/MudaTag";
import { computed, onMounted, onUnmounted, ref } from "vue";

type BluetoothStatus = "idle" | "scanning" | "connecting" | "connected" | "error";
type TagVariant = "default" | "primary" | "secondary" | "success" | "danger" | "warning" | "info";

interface Measurement {
  measured_at: string;
  weight_kg: number;
  impedance_ohm: number | null;
  device_id: string;
  source: "advertisement" | "gatt";
  raw_payload_hex: string;
}

interface StatusSnapshot {
  bluetooth: {
    status: BluetoothStatus;
    device_id: string | null;
    device_name: string | null;
    last_error: string | null;
    live_weight_kg: number | null;
    live_weight_active: boolean;
  };
  last_measurement: Measurement | null;
  server_time: string;
}

const snapshot = ref<StatusSnapshot | null>(null);
const measurements = ref<Measurement[]>([]);
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
const status = computed<BluetoothStatus>(() => snapshot.value?.bluetooth.status ?? "idle");
const statusVariant = computed<TagVariant>(() => {
  const variants: Record<BluetoothStatus, TagVariant> = {
    idle: "secondary",
    scanning: "info",
    connecting: "warning",
    connected: "success",
    error: "danger",
  };
  return variants[status.value];
});

function formatWeight(value: number | null): string {
  return value === null ? "--" : value.toFixed(2);
}

function formatTime(value: string | null | undefined): string {
  if (!value) return "No measurement yet";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "medium",
  }).format(new Date(value));
}

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

    snapshot.value = (await statusResponse.json()) as StatusSnapshot;
    const payload = (await measurementsResponse.json()) as { measurements: Measurement[] };
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
    <header class="border-muda-secondary-light mb-8 flex items-end justify-between gap-6 border-b pb-5">
      <div>
        <p class="text-muda-primary mb-2 font-mono text-xs tracking-[0.3em] uppercase">Local scale monitor</p>
        <h1 class="text-3xl font-semibold tracking-tight sm:text-4xl">eufylocal</h1>
      </div>
      <MudaTag :variant="statusVariant" size="medium" class="capitalize">{{ status }}</MudaTag>
    </header>

    <MudaErrorBox v-if="refreshError && !snapshot" title="Server unreachable" :error="refreshError" />

    <div v-else-if="loading" class="grid min-h-[50vh] place-items-center">
      <MudaSpinner size="large" label="Loading scale data" />
    </div>

    <template v-else>
      <section class="mb-6 grid gap-6 lg:grid-cols-[minmax(0,1.65fr)_minmax(18rem,1fr)]">
        <MudaCard class="overflow-hidden">
          <div class="flex min-h-72 flex-col justify-between gap-10">
            <div class="flex items-center justify-between gap-4">
              <p class="section-label">Current weight</p>
              <span v-if="liveWeight !== null" class="text-muda-success flex items-center gap-2 text-sm">
                <span class="live-dot"></span>
                Live
              </span>
            </div>

            <div>
              <div class="flex items-baseline gap-3 font-mono tabular-nums">
                <strong class="weight-value">{{ formatWeight(currentWeight) }}</strong>
                <span class="text-muda-secondary text-xl sm:text-2xl">kg</span>
              </div>
              <p class="text-muda-secondary mt-4 text-sm">
                {{ liveWeight !== null ? "Stabilizing on scale" : formatTime(currentMeasurement?.measured_at) }}
              </p>
            </div>
          </div>
        </MudaCard>

        <MudaCard>
          <div class="flex h-full flex-col">
            <p class="section-label mb-7">Bluetooth link</p>
            <dl class="info-list">
              <div>
                <dt>Device</dt>
                <dd>{{ snapshot?.bluetooth.device_name ?? "Not discovered" }}</dd>
              </div>
              <div>
                <dt>Identifier</dt>
                <dd class="font-mono text-xs">{{ snapshot?.bluetooth.device_id ?? "--" }}</dd>
              </div>
              <div>
                <dt>Last sync</dt>
                <dd>{{ formatTime(snapshot?.server_time) }}</dd>
              </div>
            </dl>
            <p v-if="snapshot?.bluetooth.last_error" class="text-muda-danger mt-auto pt-6 text-sm">
              {{ snapshot.bluetooth.last_error }}
            </p>
          </div>
        </MudaCard>
      </section>

      <MudaCard>
        <div class="mb-5 flex items-end justify-between gap-4">
          <div>
            <p class="section-label mb-2">History</p>
            <h2 class="font-semibold">Recent measurements</h2>
          </div>
          <span class="text-muda-secondary font-mono text-xs">{{ measurements.length }} records</span>
        </div>

        <div v-if="measurements.length" class="overflow-x-auto">
          <MudaTable>
            <template #head>
              <MudaTableRow>
                <MudaTableHead>Local time</MudaTableHead>
                <MudaTableHead>Weight</MudaTableHead>
                <MudaTableHead>Impedance</MudaTableHead>
                <MudaTableHead>Source</MudaTableHead>
                <MudaTableHead>Device</MudaTableHead>
              </MudaTableRow>
            </template>
            <template #body>
              <MudaTableRow v-for="measurement in measurements" :key="measurement.measured_at + measurement.device_id">
                <MudaTableCell class="whitespace-nowrap">{{ formatTime(measurement.measured_at) }}</MudaTableCell>
                <MudaTableCell class="font-mono font-semibold tabular-nums"
                  >{{ measurement.weight_kg.toFixed(2) }} kg</MudaTableCell
                >
                <MudaTableCell class="font-mono tabular-nums">
                  {{ measurement.impedance_ohm === null ? "--" : `${measurement.impedance_ohm.toFixed(1)} Ω` }}
                </MudaTableCell>
                <MudaTableCell>
                  <MudaTag size="small" variant="default">{{ measurement.source }}</MudaTag>
                </MudaTableCell>
                <MudaTableCell class="max-w-56 truncate font-mono text-xs">{{ measurement.device_id }}</MudaTableCell>
              </MudaTableRow>
            </template>
          </MudaTable>
        </div>

        <div v-else class="border-muda-secondary-light grid min-h-48 place-items-center border-t text-center">
          <div>
            <p class="font-medium">Waiting for the first measurement</p>
            <p class="text-muda-secondary mt-2 text-sm">Step on the scale to begin local history.</p>
          </div>
        </div>
      </MudaCard>
    </template>
  </main>
</template>
