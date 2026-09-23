<script setup lang="ts">
import { MudaDialog } from "@mudakit/ui";
import { computed } from "vue";

import { deleteUser, type User } from "@/api";
import ApiForm from "@/app/components/ApiForm/ApiForm.vue";
import UserBadge from "@/app/components/User/UserBadge.vue";
import { useApi } from "@/app/composables/useApi";

const user = defineModel<User | null>({ required: true });

const emit = defineEmits<{
  (e: "deleted"): void;
}>();

const mutation = useApi((id: number) => deleteUser({ path: { user_id: id }, throwOnError: true }));

const close = () => {
  user.value = null;
  mutation.reset();
};

const isOpen = computed({
  get: () => user.value != null,
  set: (value) => {
    if (!value) {
      close();
    }
  },
});

const onSubmit = () => {
  if (user.value != null) {
    void mutation.dispatch(user.value.id);
  }
};

const onDeleted = () => {
  emit("deleted");
  close();
};
</script>

<template>
  <MudaDialog v-model="isOpen">
    <ApiForm
      submit-label="Delete"
      cancel-label="Cancel"
      variant="danger"
      :state="mutation.state.value"
      :confirmation-text="user?.name"
      @submit="onSubmit"
      @cancel="close"
      @success="onDeleted"
    >
      <template #title>Delete User?</template>
      <template #form>
        <template v-if="user != null">
          <UserBadge :user="user" />
          <p class="text-muda-secondary mt-3 text-sm">Their measurements will remain in history as unassigned.</p>
        </template>
      </template>
    </ApiForm>
  </MudaDialog>
</template>
