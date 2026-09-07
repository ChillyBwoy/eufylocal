<script setup lang="ts">
import { MudaCard } from "@mudakit/ui/MudaCard";

import { type BluetoothStatusResponse } from "@/api";
import { formatTime } from "@/utils/format";

defineProps<{
  bluetooth?: BluetoothStatusResponse;
  serverTime?: string;
}>();
</script>

<template>
  <MudaCard>
    <div class="flex h-full flex-col">
      <p class="section-label mb-7">Bluetooth link</p>
      <dl class="info-list">
        <div>
          <dt>Device</dt>
          <dd>{{ bluetooth?.device_name ?? "Not discovered" }}</dd>
        </div>
        <div>
          <dt>Identifier</dt>
          <dd class="font-mono text-xs">{{ bluetooth?.device_id ?? "--" }}</dd>
        </div>
        <div>
          <dt>Last sync</dt>
          <dd>{{ formatTime(serverTime) }}</dd>
        </div>
      </dl>
      <p v-if="bluetooth?.last_error" class="text-muda-danger mt-auto pt-6 text-sm">
        {{ bluetooth.last_error }}
      </p>
    </div>
  </MudaCard>
</template>
