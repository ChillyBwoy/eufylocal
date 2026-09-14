<script setup lang="ts">
import { RouterLink } from "vue-router";

import ThemeToggle from "@/app/components/ThemeToggle/ThemeToggle.vue";
import { routes } from "@/app/router/routes";
</script>

<template>
  <header class="border-muda-secondary-light flex flex-wrap items-end justify-between gap-4">
    <div class="flex flex-col gap-2">
      <p class="text-muda-primary font-mono text-xs tracking-[0.3em] uppercase">Local scale monitor</p>
      <RouterLink :to="routes.dashboard()" class="w-fit">
        <h1 class="text-2xl font-semibold tracking-tight">eufylocal</h1>
      </RouterLink>
    </div>
    <div class="flex items-center gap-4">
      <nav class="flex items-center gap-1 text-sm" aria-label="Main navigation">
        <RouterLink
          :to="routes.dashboard()"
          class="text-muda-secondary rounded px-3 py-2"
          exact-active-class="text-muda-primary! bg-muda-primary-light"
        >
          Dashboard
        </RouterLink>
        <RouterLink
          :to="routes.users()"
          class="text-muda-secondary rounded px-3 py-2"
          active-class="text-muda-primary! bg-muda-primary-light"
        >
          Users
        </RouterLink>
      </nav>
      <ThemeToggle />
    </div>
  </header>
</template>
