<script setup lang="ts">
import { MudaButton, MudaIcon } from "@mudakit/ui";

import { useTheme } from "@/app/composables/useTheme";

const { isDark, toggleTheme } = useTheme();
</script>

<template>
  <MudaButton variant="default" size="small" @click="toggleTheme">
    <MudaIcon :icon="isDark ? 'light_mode:outlined' : 'dark_mode:outlined'" />
  </MudaButton>
</template>
