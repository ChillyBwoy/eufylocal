<script setup lang="ts">
import { MudaDropdown, type MudaDropdownItem, MudaIcon } from "@mudakit/ui";
import { computed } from "vue";

import type { Measurement } from "@/api";

const props = defineProps<{
  measurement: Measurement;
}>();

const emit = defineEmits<{
  (e: "update", measurement: Measurement): void;
  (e: "delete", measurement: Measurement): void;
}>();

const actions = computed<MudaDropdownItem<"edit" | "delete">[]>(() => [
  { id: "edit", label: "Change User", icon: "edit:filled" },
  { id: "delete", label: "Delete", icon: "delete:filled", variant: "danger" },
]);

const onAction = (item: MudaDropdownItem<"edit" | "delete">) => {
  if (item.id === "edit") {
    emit("update", props.measurement);
  } else if (item.id === "delete") {
    emit("delete", props.measurement);
  }
};
</script>

<template>
  <MudaDropdown :items="actions" @action="onAction($event)">
    <button type="button" class="flex size-8 items-center justify-center rounded">
      <MudaIcon icon="more_vert:filled" />
    </button>
  </MudaDropdown>
</template>
