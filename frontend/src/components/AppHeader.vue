<script setup lang="ts">
import ThemeToggle from "@/components/ThemeToggle.vue";
</script>

<template>
  <header class="border-muda-secondary-light mb-8 flex items-end justify-between gap-6 border-b pb-5">
    <div>
      <p class="text-muda-primary mb-2 font-mono text-xs tracking-[0.3em] uppercase">Local scale monitor</p>
      <h1 class="text-3xl font-semibold tracking-tight sm:text-4xl">eufylocal</h1>
    </div>
    <div class="flex items-center gap-3">
      <ThemeToggle />
    </div>
  </header>
</template>
