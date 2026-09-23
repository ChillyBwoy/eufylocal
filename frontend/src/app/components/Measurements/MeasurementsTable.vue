<script setup lang="ts">
import { MudaTable, MudaTableCell, MudaTableHead, MudaTableRow } from "@mudakit/ui";
import { computed, ref } from "vue";

import { type Measurement, type User } from "@/api";
import MeasurementActions from "@/app/components/Measurements/MeasurementActions.vue";
import MeasurementDeleteDialog from "@/app/components/Measurements/MeasurementDeleteDialog.vue";
import MeasurementUserDialog from "@/app/components/Measurements/MeasurementUserDialog.vue";
import { formatDateTime } from "@/common/format";

import UserBadge from "../User/UserBadge.vue";

const props = defineProps<{
  measurements: Measurement[];
  users: User[];
}>();

const emit = defineEmits<{
  (e: "updated"): void;
}>();

const measurementToUpdate = ref<Measurement | null>(null);
const measurementToDelete = ref<Measurement | null>(null);

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
  <div class="muda:no-scrollbar scroll-container-v-foreground absolute inset-6">
    <MudaTable sticky-header>
      <template #head>
        <MudaTableRow>
          <MudaTableHead class="w-[15%] text-left">Time</MudaTableHead>
          <MudaTableHead class="w-[20%] text-left">Weight</MudaTableHead>
          <MudaTableHead class="w-[20%] text-left">Impedance</MudaTableHead>
          <MudaTableHead class="text-left">User</MudaTableHead>
          <MudaTableHead class="w-14" />
        </MudaTableRow>
      </template>
      <template #body>
        <template v-for="[date, measurements] in groupedMeasurement" :key="date">
          <MudaTableRow class="border-b-0!">
            <MudaTableCell colspan="5">
              <h3 class="font-mono text-sm">{{ date }}</h3>
            </MudaTableCell>
          </MudaTableRow>
          <MudaTableRow
            v-for="(measurement, i) in measurements"
            :key="measurement.id"
            :class="[
              'group',
              {
                'border-b-0!': i < measurements.length - 1,
              },
            ]"
          >
            <MudaTableCell class="pl-4! whitespace-nowrap">
              {{ formatDateTime(measurement.measured_at, "time") }}
            </MudaTableCell>
            <MudaTableCell class="font-mono font-semibold tabular-nums">
              {{ measurement.weight.toFixed(2) }} {{ measurement.unit }}
            </MudaTableCell>

            <MudaTableCell class="font-mono tabular-nums">
              {{ measurement.impedance_ohm === null ? "--" : `${measurement.impedance_ohm.toFixed(1)} Ω` }}
            </MudaTableCell>
            <MudaTableCell>
              <UserBadge :user="measurement.user" />
            </MudaTableCell>
            <MudaTableCell>
              <div class="flex items-center justify-end">
                <MeasurementActions
                  :measurement="measurement"
                  @update="measurementToUpdate = $event"
                  @delete="measurementToDelete = $event"
                />
              </div>
            </MudaTableCell>
          </MudaTableRow>
        </template>
      </template>
    </MudaTable>
    <MeasurementUserDialog v-model="measurementToUpdate" :users="props.users" @updated="emit('updated')" />
    <MeasurementDeleteDialog v-model="measurementToDelete" @deleted="emit('updated')" />
  </div>
</template>
