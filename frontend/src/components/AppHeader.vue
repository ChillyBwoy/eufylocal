<script setup lang="ts">
import { type MudaComponentVariant } from "@mudakit/ui";
import { MudaTag } from "@mudakit/ui/MudaTag";

import { type BleStatus } from "@/api";

defineProps<{
  status: BleStatus;
  statusVariant: MudaComponentVariant;
}>();
</script>

<template>
  <header class="border-muda-secondary-light mb-8 flex items-end justify-between gap-6 border-b pb-5">
    <div>
      <p class="text-muda-primary mb-2 font-mono text-xs tracking-[0.3em] uppercase">Local scale monitor</p>
      <h1 class="text-3xl font-semibold tracking-tight sm:text-4xl">eufylocal</h1>
    </div>
    <MudaTag :variant="statusVariant" size="medium" class="capitalize">{{ status }}</MudaTag>
  </header>
</template>
