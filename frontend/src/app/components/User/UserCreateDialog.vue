<script setup lang="ts">
import { MudaColorPicker, MudaDialog, MudaFormField, MudaFormInput } from "@mudakit/ui";
import { ref } from "vue";

import { createUser, type User, type UserCreate } from "@/api";
import ApiForm from "@/app/components/ApiForm/ApiForm.vue";
import { useApi } from "@/app/composables/useApi";
import type { AppFormErrors } from "@/app/error";
import { DEFAULT_USER_COLOR } from "@/common/color";

const isOpen = defineModel<boolean>({
  required: true,
});

const emit = defineEmits<{
  (e: "created", user: User): void;
}>();

const formData = ref<Partial<UserCreate>>({
  name: "",
  color: DEFAULT_USER_COLOR,
});

const formErrors = ref<AppFormErrors<UserCreate>>();

const mutation = useApi(() => createUser({ body: formData.value as UserCreate, throwOnError: true }));

const close = () => {
  isOpen.value = false;
  formData.value = {
    name: "",
    color: DEFAULT_USER_COLOR,
  };
  formErrors.value = undefined;
  mutation.reset();
};

const onCreated = (user: User) => {
  emit("created", user);
  close();
};
</script>

<template>
  <MudaDialog v-model="isOpen">
    <ApiForm
      v-model:errors="formErrors"
      submit-label="Create"
      cancel-label="Cancel"
      :state="mutation.state.value"
      @submit="() => void mutation.dispatch()"
      @cancel="close"
      @success="onCreated($event)"
    >
      <template #title>Create User</template>
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
