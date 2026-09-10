<script setup lang="ts">
import { MudaErrorBox } from "@mudakit/ui/MudaErrorBox";
import { MudaSpinner } from "@mudakit/ui/MudaSpinner";
import { computed, onMounted, ref } from "vue";

import { getMeasurements } from "@/api";
import AppHeader from "@/components/AppHeader.vue";
import CurrentWeightCard from "@/components/CurrentWeightCard.vue";
import MeasurementHistoryCard from "@/components/MeasurementHistoryCard.vue";
import UseApiState from "@/components/UseApiState.vue";
import { useApi } from "@/composables/useApi";
import { type ServerSideStatusMessage, useServerEvents } from "@/composables/useServerEvents";

const { dispatch, state } = useApi(() => getMeasurements({ query: { limit: 50 }, throwOnError: true }));
const liveMeasurement = ref<ServerSideStatusMessage | null>(null);

const serverEvents = useServerEvents(
  (message) => {
    liveMeasurement.value = message;
  },
  async () => {
    await dispatch();
  },
);

const currentMeasurement = computed(() => {
  if (state.value.status === "idle") {
    return null;
  }

  const measurements = state.value.status === "success" ? state.value.result : state.value.prevResult;
  return measurements?.[0] ?? null;
});

const liveWeight = computed(() => liveMeasurement.value?.weight ?? null);
const currentWeight = computed(() => liveWeight.value ?? currentMeasurement.value?.weight ?? null);
const currentUnit = computed(() => liveMeasurement.value?.unit ?? currentMeasurement.value?.unit ?? "kg");

onMounted(async () => {
  serverEvents.start();
  await dispatch();
});
</script>

<template>
  <main class="mx-auto grid h-full w-full max-w-6xl grid-rows-[auto_1fr] p-6">
    <AppHeader />

    <UseApiState :state="state">
      <template #idle>
        <div class="grid min-h-[50vh] place-items-center">
          <MudaSpinner size="large" label="Loading scale data" />
        </div>
      </template>

      <template #loading>
        <div class="grid min-h-[50vh] place-items-center">
          <MudaSpinner size="large" label="Loading scale data" />
        </div>
      </template>

      <template #failure="{ error }">
        <MudaErrorBox title="Server unreachable" :error="error" />
      </template>

      <template #body="{ result }">
        <div class="grid h-full grid-rows-[auto_1fr] gap-4">
          <CurrentWeightCard
            :weight="currentWeight"
            :live-weight="liveWeight"
            :unit="currentUnit"
            :measured-at="currentMeasurement?.measured_at"
          />

          <MeasurementHistoryCard :measurements="result" class="h-full" />
        </div>
      </template>
    </UseApiState>
  </main>
</template>
