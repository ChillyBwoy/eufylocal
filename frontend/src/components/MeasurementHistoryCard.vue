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
  <MudaCard v-if="measurements.length" class="relative">
    <div class="muda:no-scrollbar scroll-container-v-foreground absolute inset-6">
      <MudaTable sticky-header>
        <template #head>
          <MudaTableRow>
            <MudaTableHead class="w-[15%] text-left">Time</MudaTableHead>
            <MudaTableHead class="w-[30%] text-left">Weight</MudaTableHead>
            <MudaTableHead class="text-left">Impedance</MudaTableHead>
          </MudaTableRow>
        </template>
        <template #body>
          <template v-for="[date, measurements] in groupedMeasurement" :key="date">
            <MudaTableRow class="border-b-0!">
              <MudaTableCell colspan="3">
                <h3 class="font-mono text-sm">{{ date }}</h3>
              </MudaTableCell>
            </MudaTableRow>
            <MudaTableRow
              v-for="(measurement, i) in measurements"
              :key="measurement.id"
              :class="{
                'border-b-0!': i < measurements.length - 1,
              }"
            >
              <MudaTableCell class="pl-4! whitespace-nowrap">{{ formatTime(measurement.measured_at) }}</MudaTableCell>
              <MudaTableCell class="font-mono font-semibold tabular-nums">
                {{ measurement.weight.toFixed(2) }} {{ measurement.unit }}
              </MudaTableCell>
              <MudaTableCell class="font-mono tabular-nums">
                {{ measurement.impedance_ohm === null ? "--" : `${measurement.impedance_ohm.toFixed(1)} Ω` }}
              </MudaTableCell>
            </MudaTableRow>
          </template>
        </template>
      </MudaTable>
    </div>
  </MudaCard>

  <MudaCard v-else class="border-muda-secondary-light grid min-h-48 place-items-center border-t text-center">
    <div>
      <p class="font-medium">Waiting for the first measurement</p>
      <p class="text-muda-secondary mt-2 text-sm">Step on the scale to begin local history.</p>
    </div>
  </MudaCard>
</template>
