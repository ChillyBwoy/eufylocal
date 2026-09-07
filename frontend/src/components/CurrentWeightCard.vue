<script setup lang="ts">
import { MudaCard } from "@mudakit/ui/MudaCard";

import { formatTime, formatWeight } from "@/utils/format";

defineProps<{
  weight: number | null;
  liveWeight: number | null;
  measuredAt: string | null | undefined;
}>();
</script>

<template>
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
          <strong class="weight-value">{{ formatWeight(weight) }}</strong>
          <span class="text-muda-secondary text-xl sm:text-2xl">kg</span>
        </div>
        <p class="text-muda-secondary mt-4 text-sm">
          {{ liveWeight !== null ? "Stabilizing on scale" : formatTime(measuredAt) }}
        </p>
      </div>
    </div>
  </MudaCard>
</template>
