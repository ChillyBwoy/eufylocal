<script setup lang="ts">
import { MudaColorPicker, MudaDialog, MudaFormField, MudaFormInput } from "@mudakit/ui";
import { computed, ref, watch } from "vue";

import { updateUser, type User } from "@/api";
import ApiForm from "@/app/components/ApiForm/ApiForm.vue";
import { useApi } from "@/app/composables/useApi";
import type { AppFormErrors } from "@/app/error";

const user = defineModel<User | null>({ required: true });
type UserFormData = Pick<User, "name" | "color">;

const emit = defineEmits<{
  (e: "updated", user: User): void;
}>();

const isOpen = computed({
  get: () => user.value != null,
  set: () => {
    user.value = null;
  },
});

const formData = ref<UserFormData>({
  name: "",
  color: "",
});

const formErrors = ref<AppFormErrors<UserFormData>>();

const mutation = useApi((id: number) =>
  updateUser({
    path: { user_id: id },
    body: formData.value,
    throwOnError: true,
  }),
);

const close = () => {
  user.value = null;
  formData.value = {
    name: "",
    color: "",
  };
  formErrors.value = undefined;
  mutation.reset();
};

const onSubmit = () => {
  if (user.value != null) {
    void mutation.dispatch(user.value.id);
  }
};

const onUpdated = (updatedUser: User) => {
  emit("updated", updatedUser);
  close();
};

watch(
  user,
  (newUser) => {
    if (newUser != null) {
      formErrors.value = undefined;
      mutation.reset();
      formData.value = {
        name: newUser.name,
        color: newUser.color,
      };
    }
  },
  {
    immediate: true,
  },
);
</script>

<template>
  <MudaDialog v-model="isOpen">
    <ApiForm
      v-model:errors="formErrors"
      submit-label="Save"
      cancel-label="Cancel"
      :state="mutation.state.value"
      @submit="onSubmit"
      @cancel="close"
      @success="onUpdated($event)"
    >
      <template #title>Edit User</template>
      <template #form>
        <MudaFormField :errors="formErrors?.name">
          <template #label>Name</template>
          <MudaFormInput v-model="formData.name" autofocus />
        </MudaFormField>

        <MudaFormField :errors="formErrors?.color">
          <template #label>Color</template>
          <MudaColorPicker v-model="formData.color" />
        </MudaFormField>
      </template>
    </ApiForm>
  </MudaDialog>
</template>
