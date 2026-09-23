<script setup lang="ts">
import { RouterView } from "vue-router";

import AppHeader from "@/app/components/AppHeader/AppHeader.vue";
</script>

<template>
  <main class="mx-auto grid h-full w-full max-w-6xl grid-rows-[auto_1fr] gap-4 p-6">
    <AppHeader />
    <RouterView />
  </main>
</template>
