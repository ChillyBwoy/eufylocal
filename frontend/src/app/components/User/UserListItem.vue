<script setup lang="ts">
import { MudaCard, MudaDropdown, type MudaDropdownItem, MudaIcon } from "@mudakit/ui";
import { computed } from "vue";

import type { User } from "@/api";
import UserBadge from "@/app/components/User/UserBadge.vue";

const props = defineProps<{
  user: User;
}>();

const emit = defineEmits<{
  (e: "update", user: User): void;
  (e: "delete", user: User): void;
}>();

const actions = computed<MudaDropdownItem<"edit" | "delete">[]>(() => [
  { id: "edit", label: "Edit", icon: "edit:filled", variant: "warning" },
  { id: "delete", label: "Delete", icon: "delete:filled", variant: "danger" },
]);

const onAction = (item: MudaDropdownItem<"edit" | "delete">) => {
  if (item.id === "edit") {
    emit("update", props.user);
  } else if (item.id === "delete") {
    emit("delete", props.user);
  }
};
</script>

<template>
  <MudaCard>
    <div class="grid grid-cols-[1fr_auto] items-center gap-2">
      <UserBadge :user="props.user" />
      <MudaDropdown :items="actions" @action="onAction($event)">
        <button type="button" class="flex h-full items-center group-hover:visible">
          <MudaIcon icon="more_vert:filled" />
        </button>
      </MudaDropdown>
    </div>
  </MudaCard>
</template>
