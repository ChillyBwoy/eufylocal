<script setup lang="ts">
import ThemeToggle from "@/components/ThemeToggle.vue";
</script>

<template>
  <header class="border-muda-secondary-light flex items-end justify-between">
    <div class="flex flex-col gap-2">
      <p class="text-muda-primary font-mono text-xs tracking-[0.3em] uppercase">Local scale monitor</p>
      <h1 class="text-2xl font-semibold tracking-tight">eufylocal</h1>
    </div>
    <ThemeToggle />
  </header>
</template>
