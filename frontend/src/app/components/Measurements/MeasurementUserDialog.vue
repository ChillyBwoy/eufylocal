<script setup lang="ts">
import { MudaDialog, MudaFormField, MudaFormSelect } from "@mudakit/ui";
import { computed, ref, watch } from "vue";

import { type Measurement, updateMeasurement, type User } from "@/api";
import ApiForm from "@/app/components/ApiForm/ApiForm.vue";
import { useApi } from "@/app/composables/useApi";
import { formatDateTime } from "@/common/format";

const measurement = defineModel<Measurement | null>({ required: true });

const props = defineProps<{
  users: User[];
}>();

const emit = defineEmits<{
  (e: "updated", measurement: Measurement): void;
}>();

const selectedUserId = ref<number | null>(null);

const isOpen = computed({
  get: () => measurement.value != null,
  set: (value) => {
    if (!value) {
      close();
    }
  },
});

const measurementSummary = computed(() => {
  if (measurement.value == null) {
    return "";
  }

  return `${measurement.value.weight.toFixed(2)} ${measurement.value.unit} · ${formatDateTime(measurement.value.measured_at, "datetime")}`;
});

const mutation = useApi((measurementId: number, userId: number | null) =>
  updateMeasurement({
    path: { measurement_id: measurementId },
    body: { user_id: userId },
    throwOnError: true,
  }),
);

function close() {
  measurement.value = null;
  selectedUserId.value = null;
  mutation.reset();
}

const onSubmit = () => {
  if (measurement.value != null) {
    void mutation.dispatch(measurement.value.id, selectedUserId.value);
  }
};

const onUpdated = (updatedMeasurement: Measurement) => {
  emit("updated", updatedMeasurement);
  close();
};

watch(measurement, (newMeasurement) => {
  if (newMeasurement != null) {
    selectedUserId.value = newMeasurement.user?.id ?? null;
    mutation.reset();
  }
});
</script>

<template>
  <MudaDialog v-model="isOpen">
    <ApiForm
      submit-label="Save"
      cancel-label="Cancel"
      :state="mutation.state.value"
      @submit="onSubmit"
      @cancel="close"
      @success="onUpdated"
    >
      <template #title>Change user</template>
      <template #form>
        <p class="text-muda-secondary text-sm">{{ measurementSummary }}</p>
        <MudaFormField>
          <template #label>User</template>
          <MudaFormSelect v-model="selectedUserId">
            <option :value="null">Unassigned</option>
            <option v-for="user in props.users" :key="user.id" :value="user.id">{{ user.name }}</option>
          </MudaFormSelect>
        </MudaFormField>
      </template>
    </ApiForm>
  </MudaDialog>
</template>
