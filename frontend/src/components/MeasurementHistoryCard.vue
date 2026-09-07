<script setup lang="ts">
import { MudaCard } from "@mudakit/ui/MudaCard";
import { MudaTable, MudaTableCell, MudaTableHead, MudaTableRow } from "@mudakit/ui/MudaTable";
import { MudaTag } from "@mudakit/ui/MudaTag";

import { type MeasurementResponse } from "@/api";
import { formatTime } from "@/utils/format";

defineProps<{
  measurements: MeasurementResponse[];
}>();
</script>

<template>
  <MudaCard>
    <div class="mb-5 flex items-end justify-between gap-4">
      <div>
        <p class="text-muda-secondary mb-2 font-mono text-xs tracking-[0.22em] uppercase">History</p>
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
