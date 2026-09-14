<script setup lang="ts">
import { MudaCard } from "@mudakit/ui/MudaCard";
import { computed } from "vue";

import { type MeasurementUnit, type User } from "@/api";
import { formatDateTime, formatWeight } from "@/common/format";
import UserBadge from "@/components/UserBadge.vue";

const props = defineProps<{
  weight: number | null;
  liveWeight: number | null;
  unit: MeasurementUnit;
  measuredAt: string | null;
  user: User | null;
}>();

const measuredAtFormatted = computed(() => {
  if (props.liveWeight != null) {
    return "Stabilizing on scale";
  }
  return props.measuredAt != null ? formatDateTime(props.measuredAt, "datetime") : "No measurement yet";
});
</script>

<template>
  <MudaCard class="overflow-hidden">
    <div class="flex flex-col justify-between gap-6">
      <div class="flex items-center justify-between gap-4">
        <p class="text-muda-secondary font-mono text-xs tracking-[0.22em] uppercase">Current weight</p>
        <span v-if="liveWeight !== null" class="text-muda-success flex items-center gap-2 text-sm">
          <span class="bg-muda-success animate-pulse-ring size-2 rounded-full motion-reduce:animate-none"></span>
          Live
        </span>
        <UserBadge v-else :user="user" />
      </div>

      <div>
        <div class="flex items-baseline justify-center gap-2 font-mono">
          <strong class="text-8xl">
            {{ formatWeight(weight) }}
          </strong>
          <span class="text-muda-secondary text-4xl">{{ unit }}</span>
        </div>
        <p class="text-muda-secondary mt-4 text-sm">
          {{ measuredAtFormatted }}
        </p>
      </div>
    </div>
  </MudaCard>
</template>
