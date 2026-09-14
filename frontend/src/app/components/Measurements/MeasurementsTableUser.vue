<script setup lang="ts">
import { MudaFormSelect } from "@mudakit/ui";
import { watch } from "vue";

import { type Measurement, updateMeasurement, type User } from "@/api";
import { useApi } from "@/app/composables/useApi";

const props = defineProps<{
  measurement: Measurement;
  users: User[];
}>();

const emit = defineEmits<{
  (e: "updated"): void;
}>();

const mutation = useApi((userId: number | null) =>
  updateMeasurement({
    path: { measurement_id: props.measurement.id },
    body: { user_id: userId },
    throwOnError: true,
  }),
);

const onUpdate = async (value: string | number | null) => {
  if (typeof value === "string") {
    return;
  }

  mutation.reset();
  await mutation.dispatch(value);
};

watch(
  () => mutation.state.value,
  (state) => {
    if (state.status === "success") {
      emit("updated");
    }
  },
);
</script>

<template>
  <MudaFormSelect
    :model-value="props.measurement.user?.id ?? null"
    :disabled="props.users == null || mutation.state.value.status === 'loading'"
    append-to-body
    @update:model-value="onUpdate"
  >
    <option :value="null" />
    <option v-for="user in props.users" :key="user.id" :value="user.id">{{ user.name }}</option>
  </MudaFormSelect>
</template>
