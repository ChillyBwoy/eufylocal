<script setup lang="ts">
import { type MudaComponentVariant } from "@mudakit/ui";
import { MudaErrorBox } from "@mudakit/ui/MudaErrorBox";
import { MudaSpinner } from "@mudakit/ui/MudaSpinner";
import { computed, onMounted } from "vue";

import { type BleStatus, getMeasurements, getStatus } from "@/api";
import AppHeader from "@/components/AppHeader.vue";
import BluetoothStatusCard from "@/components/BluetoothStatusCard.vue";
import CurrentWeightCard from "@/components/CurrentWeightCard.vue";
import MeasurementHistoryCard from "@/components/MeasurementHistoryCard.vue";
import { useApi } from "@/composables/useApi";

const { start: startPolling, state } = useApi.poll(
  () =>
    useApi.all({
      measurements: getMeasurements({ query: { limit: 50 }, throwOnError: true }),
      snapshot: getStatus({ throwOnError: true }),
    }),
  3_000,
);

const currentMeasurement = computed(() => {
  if (state.value.status === "idle") {
    return null;
  }

  const data = state.value.status === "success" ? state.value.result : state.value.prevResult;
  return data?.snapshot.last_measurement ?? data?.measurements[0] ?? null;
});

const liveWeight = computed(() => {
  if (state.value.status === "idle") {
    return null;
  }

  const data = state.value.status === "success" ? state.value.result : state.value.prevResult;
  const bluetooth = data?.snapshot.bluetooth;
  return bluetooth?.live_weight_active ? bluetooth.live_weight_kg : null;
});

const currentWeight = computed(() => liveWeight.value ?? currentMeasurement.value?.weight_kg ?? null);

const status = computed<BleStatus>(() => {
  if (state.value.status === "idle") {
    return "idle";
  }

  const data = state.value.status === "success" ? state.value.result : state.value.prevResult;

  return data?.snapshot.bluetooth.status ?? "idle";
});

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

onMounted(() => void startPolling());
</script>

<template>
  <main class="mx-auto h-full w-full max-w-6xl p-6">
    <AppHeader :status="status" :status-variant="statusVariant" />

    <MudaErrorBox
      v-if="state.status === 'failure' && !state.prevResult"
      title="Server unreachable"
      :error="state.error"
    />

    <div
      v-else-if="state.status === 'idle' || (state.status === 'loading' && !state.prevResult)"
      class="grid min-h-[50vh] place-items-center"
    >
      <MudaSpinner size="large" label="Loading scale data" />
    </div>

    <template v-else>
      <section class="mb-6 grid gap-6 lg:grid-cols-[minmax(0,1.65fr)_minmax(18rem,1fr)]">
        <CurrentWeightCard
          :weight="currentWeight"
          :live-weight="liveWeight"
          :measured-at="currentMeasurement?.measured_at"
        />
        <BluetoothStatusCard
          :bluetooth="
            state.status === 'success'
              ? state.result.snapshot.bluetooth
              : (state.prevResult?.snapshot.bluetooth ?? null)
          "
          :server-time="
            state.status === 'success'
              ? state.result.snapshot.server_time
              : (state.prevResult?.snapshot.server_time ?? null)
          "
        />
      </section>

      <MeasurementHistoryCard
        :measurements="state.status === 'success' ? state.result.measurements : (state.prevResult?.measurements ?? [])"
      />
    </template>
  </main>
</template>
