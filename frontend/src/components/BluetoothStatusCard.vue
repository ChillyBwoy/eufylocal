<script setup lang="ts">
import { MudaCard } from "@mudakit/ui/MudaCard";

import { type BluetoothStatus } from "@/api";
import { formatTime } from "@/utils/format";

defineProps<{
  bluetooth: BluetoothStatus | null;
  serverTime: string | null;
}>();
</script>

<template>
  <MudaCard>
    <div class="flex h-full flex-col">
      <p class="text-muda-secondary mb-7 font-mono text-xs tracking-[0.22em] uppercase">Bluetooth link</p>
      <dl class="grid gap-5">
        <div class="border-muda-secondary-light border-b pb-4 last:border-0">
          <dt class="text-muda-secondary mb-1 text-xs tracking-wider uppercase">Device</dt>
          <dd class="m-0 font-medium break-all">{{ bluetooth?.device_name ?? "Not discovered" }}</dd>
        </div>
        <div class="border-muda-secondary-light border-b pb-4 last:border-0">
          <dt class="text-muda-secondary mb-1 text-xs tracking-wider uppercase">Identifier</dt>
          <dd class="m-0 font-mono text-xs font-medium break-all">{{ bluetooth?.device_id ?? "--" }}</dd>
        </div>
        <div class="border-muda-secondary-light border-b pb-4 last:border-0">
          <dt class="text-muda-secondary mb-1 text-xs tracking-wider uppercase">Last sync</dt>
          <dd class="m-0 font-medium break-all">{{ formatTime(serverTime) }}</dd>
        </div>
      </dl>
      <p v-if="bluetooth?.last_error" class="text-muda-danger mt-auto pt-6 text-sm">
        {{ bluetooth.last_error }}
      </p>
    </div>
  </MudaCard>
</template>
