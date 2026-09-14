<script setup lang="ts">
import { MudaMarker } from "@mudakit/ui";

import type { User } from "@/api";
import { DEFAULT_USER_COLOR } from "@/common/color";

defineProps<{
  user: User | null;
}>();
</script>

<template>
  <span class="inline-flex min-w-0 items-center gap-2 text-sm">
    <MudaMarker :color="user == null ? DEFAULT_USER_COLOR : user.color" />
    <span class="truncate">{{ user?.name ?? "Unassigned" }}</span>
  </span>
</template>
