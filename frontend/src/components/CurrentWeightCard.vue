<script setup lang="ts">
import { MudaCard } from "@mudakit/ui/MudaCard";

import { formatDateTime, formatWeight } from "@/common/format";

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
        <p class="text-muda-secondary font-mono text-xs tracking-[0.22em] uppercase">Current weight</p>
        <span v-if="liveWeight !== null" class="text-muda-success flex items-center gap-2 text-sm">
          <span class="bg-muda-success animate-pulse-ring size-2 rounded-full motion-reduce:animate-none"></span>
          Live
        </span>
      </div>

      <div>
        <div class="flex items-baseline gap-3 font-mono tabular-nums">
          <strong class="text-[clamp(4rem,13vw,8.5rem)] leading-[0.85] tracking-[-0.09em]">
            {{ formatWeight(weight) }}
          </strong>
          <span class="text-muda-secondary text-xl sm:text-2xl">kg</span>
        </div>
        <p class="text-muda-secondary mt-4 text-sm">
          {{ liveWeight !== null ? "Stabilizing on scale" : formatDateTime(measuredAt) }}
        </p>
      </div>
    </div>
  </MudaCard>
</template>
