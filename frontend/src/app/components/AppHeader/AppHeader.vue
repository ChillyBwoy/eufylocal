<script setup lang="ts">
import { MudaIcon } from "@mudakit/ui";
import { RouterLink } from "vue-router";

import ThemeToggle from "@/app/components/ThemeToggle/ThemeToggle.vue";
import { routes } from "@/app/router/routes";
</script>

<template>
  <header class="border-muda-secondary-light flex flex-col gap-2 border-b">
    <div class="flex items-center justify-between gap-4">
      <div class="flex flex-col gap-1">
        <p class="text-muda-primary font-mono text-xs tracking-[0.3em] uppercase">Local scale monitor</p>
        <RouterLink :to="routes.dashboard()" class="w-fit">
          <h1 class="text-2xl font-semibold tracking-tight">eufylocal</h1>
        </RouterLink>
      </div>
      <ThemeToggle />
    </div>

    <nav class="flex items-center gap-4 text-sm">
      <RouterLink
        :to="routes.dashboard()"
        class="text-muda-secondary -mb-px flex items-center gap-2 border-b-2 border-transparent px-0.5 py-3"
        exact-active-class="text-muda-primary! border-muda-primary!"
      >
        <MudaIcon icon="dashboard:outlined" />
        Dashboard
      </RouterLink>
      <RouterLink
        :to="routes.users()"
        class="text-muda-secondary -mb-px flex items-center gap-2 border-b-2 border-transparent px-0.5 py-3"
        active-class="text-muda-primary! border-muda-primary!"
      >
        <MudaIcon icon="family_restroom:outlined" />
        Users
      </RouterLink>
    </nav>
  </header>
</template>
