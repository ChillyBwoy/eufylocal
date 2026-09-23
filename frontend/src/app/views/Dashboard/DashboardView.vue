<script setup lang="ts">
import { MudaCard, MudaErrorBox } from "@mudakit/ui";
import { computed, onMounted, ref } from "vue";

import { getMeasurements, getUsers } from "@/api";
import ApiResult from "@/app/components/ApiResult/ApiResult.vue";
import CurrentWeight from "@/app/components/CurrentWeight/CurrentWeight.vue";
import MeasurementsChart from "@/app/components/Measurements/MeasurementsChart.vue";
import MeasurementsTable from "@/app/components/Measurements/MeasurementsTable.vue";
import { useApi } from "@/app/composables/useApi";
import { type ServerSideStatusMessage, useServerEvents } from "@/app/composables/useServerEvents";

import DashboardLoader from "./DashboardLoader.vue";

const fetchMeasurements = useApi(() => getMeasurements({ query: { limit: 50 }, throwOnError: true }));
const fetchUsers = useApi(() => getUsers({ throwOnError: true }));
const liveMeasurement = ref<ServerSideStatusMessage | null>(null);

const serverEvents = useServerEvents(
  (message) => {
    liveMeasurement.value = message;
  },
  async () => {
    await fetchMeasurements.dispatch();
  },
);

const currentMeasurement = computed(() => {
  if (fetchMeasurements.state.value.status === "idle") {
    return null;
  }

  const items =
    fetchMeasurements.state.value.status === "success"
      ? fetchMeasurements.state.value.result
      : fetchMeasurements.state.value.prevResult;
  return items?.[0] ?? null;
});

const liveWeight = computed(() => liveMeasurement.value?.weight ?? null);
const currentWeight = computed(() => liveWeight.value ?? currentMeasurement.value?.weight ?? null);
const currentUnit = computed(() => liveMeasurement.value?.unit ?? currentMeasurement.value?.unit ?? "kg");

onMounted(async () => {
  serverEvents.start();
  await Promise.all([fetchUsers.dispatch(), fetchMeasurements.dispatch()]);
});
</script>

<template>
  <ApiResult :state="fetchUsers.state.value">
    <template #idle>
      <DashboardLoader />
    </template>

    <template #loading>
      <DashboardLoader />
    </template>
    <template #failure="{ error }">
      <MudaErrorBox title="Server unreachable" :error="error" />
    </template>
    <template #body="{ result: users }">
      <ApiResult :state="fetchMeasurements.state.value">
        <template #idle>
          <DashboardLoader />
        </template>

        <template #loading>
          <DashboardLoader />
        </template>

        <template #failure="{ error }">
          <MudaErrorBox title="Server unreachable" :error="error" />
        </template>

        <template #body="{ result: measurements }">
          <div class="grid h-full grid-rows-[auto_1fr] gap-4">
            <div class="grid grid-cols-[auto_2fr] gap-4">
              <MudaCard class="overflow-hidden">
                <CurrentWeight
                  :weight="currentWeight"
                  :live-weight="liveWeight"
                  :unit="currentUnit"
                  :measured-at="currentMeasurement?.measured_at ?? null"
                  :user="currentMeasurement?.user ?? null"
                />
              </MudaCard>
              <MudaCard>
                <MeasurementsChart :measurements="measurements" />
              </MudaCard>
            </div>

            <MudaCard v-if="measurements.length > 0" class="relative h-full">
              <MeasurementsTable
                :measurements="measurements"
                :users="users"
                @updated="() => void fetchMeasurements.dispatch()"
              />
            </MudaCard>
            <MudaCard v-else class="border-muda-secondary-light grid min-h-48 place-items-center border-t text-center">
              <div>
                <p class="font-medium">Waiting for the first measurement</p>
                <p class="text-muda-secondary mt-2 text-sm">Step on the scale to begin local history.</p>
              </div>
            </MudaCard>
          </div>
        </template>
      </ApiResult>
    </template>
  </ApiResult>
</template>
