<script setup lang="ts">
import { MudaButton, MudaDialog } from "@mudakit/ui";
import { computed } from "vue";

import { deleteMeasurement, type Measurement } from "@/api";
import UserBadge from "@/app/components/User/UserBadge.vue";
import { useAsyncCall } from "@/app/composables/useAsyncCall";
import { formatDateTime } from "@/common/format";

const measurement = defineModel<Measurement | null>({
  required: true,
});

const emit = defineEmits<{
  (e: "deleted"): void;
}>();

const isOpen = computed({
  get: () => measurement.value != null,
  set: () => {
    measurement.value = null;
  },
});

const mutation = useAsyncCall(async ({ signal }, id: number) => {
  const { data } = await deleteMeasurement({ path: { measurement_id: id }, signal, throwOnError: true });
  return data;
});

const onDelete = async () => {
  if (measurement.value == null) {
    return;
  }
  await mutation.dispatch(measurement.value.id);
  emit("deleted");
  measurement.value = null;
};
</script>

<template>
  <MudaDialog v-model="isOpen">
    <div class="flex flex-col gap-2">
      <h2>Delete Measurement?</h2>
      <template v-if="measurement != null">
        <UserBadge :user="measurement.user" />
        <p>{{ measurement.weight.toFixed(2) }} {{ measurement.unit }}</p>
        <p>{{ formatDateTime(measurement.measured_at, "datetime") }}</p>
      </template>

      <div class="flex justify-end gap-4">
        <MudaButton type="button" :disabled="mutation.state.value.status === 'loading'" @click="measurement = null">
          Cancel
        </MudaButton>
        <MudaButton
          type="submit"
          variant="danger"
          :disabled="mutation.state.value.status === 'loading'"
          @click="onDelete"
        >
          Delete
        </MudaButton>
      </div>
    </div>
  </MudaDialog>
</template>
