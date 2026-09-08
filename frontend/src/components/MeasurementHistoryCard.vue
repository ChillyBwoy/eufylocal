<script setup lang="ts">
import { MudaCard } from "@mudakit/ui/MudaCard";
import { MudaTable, MudaTableCell, MudaTableHead, MudaTableRow } from "@mudakit/ui/MudaTable";
import { computed } from "vue";

import { type Measurement } from "@/api";
import { formatTime } from "@/common/format";

const props = defineProps<{
  measurements: Measurement[];
}>();

const dateFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
});

const groupedMeasurement = computed(() => {
  const groups = new Map<string, Measurement[]>();

  for (const measure of props.measurements) {
    const date = dateFormatter.format(new Date(measure.measured_at));
    const group = groups.get(date) ?? [];
    group.push(measure);
    groups.set(date, group);
  }

  return groups;
});
</script>

<template>
  <div v-if="measurements.length" class="flex flex-col gap-4">
    <template v-for="([date, measurements], idx) in groupedMeasurement" :key="date">
      <h3 class="px-4 font-mono text-xl font-semibold">{{ date }}</h3>
      <MudaCard class="flex flex-col gap-4 overflow-x-auto">
        <MudaTable>
          <template v-if="idx === 0" #head>
            <MudaTableRow>
              <MudaTableHead class="text-left">Time</MudaTableHead>
              <MudaTableHead class="text-left">Weight</MudaTableHead>
              <MudaTableHead class="text-left">Impedance</MudaTableHead>
            </MudaTableRow>
          </template>
          <template #body>
            <MudaTableRow v-for="measurement in measurements" :key="measurement.measured_at + measurement.device_id">
              <MudaTableCell class="w-[15%] whitespace-nowrap">{{ formatTime(measurement.measured_at) }}</MudaTableCell>
              <MudaTableCell class="font-mono font-semibold tabular-nums">
                {{ measurement.weight_kg.toFixed(2) }} kg
              </MudaTableCell>
              <MudaTableCell class="font-mono tabular-nums">
                {{ measurement.impedance_ohm === null ? "--" : `${measurement.impedance_ohm.toFixed(1)} Ω` }}
              </MudaTableCell>
            </MudaTableRow>
          </template>
        </MudaTable>
      </MudaCard>
    </template>
  </div>

  <MudaCard v-else class="border-muda-secondary-light grid min-h-48 place-items-center border-t text-center">
    <div>
      <p class="font-medium">Waiting for the first measurement</p>
      <p class="text-muda-secondary mt-2 text-sm">Step on the scale to begin local history.</p>
    </div>
  </MudaCard>
</template>
