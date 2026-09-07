<script setup lang="ts">
import { MudaButton } from "@mudakit/ui/MudaButton";
import { MudaIcon } from "@mudakit/ui/MudaIcon";

import { useTheme } from "@/composables/useTheme";

const { isDark, toggleTheme } = useTheme();
</script>

<template>
  <MudaButton variant="default" size="small" @click="toggleTheme">
    <MudaIcon :icon="isDark ? 'light_mode:outlined' : 'dark_mode:outlined'" />
  </MudaButton>
</template>
