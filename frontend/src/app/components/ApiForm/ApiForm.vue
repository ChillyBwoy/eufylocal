<script setup lang="ts" generic="TResult, TFormFields extends Record<string, any>">
import type { MudaComponentVariant } from "@mudakit/ui";
import { MudaButton } from "@mudakit/ui/MudaButton";
import { MudaFormFieldErrors } from "@mudakit/ui/MudaFormField";
import { MudaFormInput } from "@mudakit/ui/MudaFormInput";
import { MudaSpinner } from "@mudakit/ui/MudaSpinner";
import { computed, type PropType, ref, watch } from "vue";

import type { UseApiState } from "@/app/composables/useApi";
import { type AppFormErrors, isAPIPlainError, isAPIValidationError, mapFormValidationErrors } from "@/app/error";

const props = withDefaults(
  defineProps<{
    state: UseApiState<TResult>;
    submitLabel?: string;
    resetLabel?: string;
    cancelLabel?: string;
    variant?: MudaComponentVariant;
    disabled?: boolean;
    confirmationText?: string;
  }>(),
  {
    variant: "primary",
  },
);

const emit = defineEmits<{
  (e: "cancel"): void;
  (e: "reset"): void;
  (e: "submit", event: SubmitEvent): void;
  (e: "success", result: TResult): void;
}>();

const errors = defineModel("errors", {
  type: Object as PropType<AppFormErrors<TFormFields> | null>,
  default: null,
});

const formError = ref<string | null>(null);

const confirmationTextValue = ref("");

const isDisabled = computed(() => {
  if (props.confirmationText != null) {
    return confirmationTextValue.value !== props.confirmationText;
  }
  return props.disabled;
});

const isLoading = computed(() => props.state.status === "loading");

const onSubmit = (event: Event) => {
  event.preventDefault();
  emit("submit", event as SubmitEvent);
};

const hasLoader = computed(() => props.cancelLabel != null || props.resetLabel != null || props.submitLabel != null);

watch(
  () => props.state,
  (newState) => {
    if (newState.status === "success") {
      errors.value = null;
      emit("success", newState.result);
    } else if (newState.status === "failure") {
      if (isAPIValidationError(newState.error)) {
        errors.value = mapFormValidationErrors(newState.error);
        formError.value = null;
      } else if (isAPIPlainError(newState.error)) {
        errors.value = null;
        formError.value = newState.error.detail;
      } else {
        errors.value = null;
        formError.value = "Unknown Error";
      }
    }
  },
);
</script>

<template>
  <form class="flex flex-col gap-2" @submit="onSubmit">
    <h2>
      <slot name="title" />
    </h2>

    <MudaFormFieldErrors v-if="formError != null" :errors="[{ message: formError }]" />

    <slot name="form" :is-loading="isLoading" />

    <template v-if="props.confirmationText != null">
      <p>
        To confirm, type <span class="font-bold">{{ props.confirmationText }}</span> in the box below
      </p>
      <MudaFormInput v-model="confirmationTextValue" />
    </template>

    <div class="flex justify-end gap-4">
      <slot name="actionsBefore" />
      <MudaSpinner v-if="hasLoader && isLoading" size="small" />
      <MudaButton v-if="props.cancelLabel != null" type="button" :disabled="isLoading" @click="emit('cancel')">
        {{ props.cancelLabel }}
      </MudaButton>
      <MudaButton v-if="props.resetLabel != null" type="reset" :disabled="isLoading" @click="emit('reset')">
        {{ props.resetLabel }}
      </MudaButton>
      <MudaButton
        v-if="props.submitLabel != null"
        type="submit"
        :variant="props.variant"
        :disabled="isDisabled || isLoading"
      >
        {{ props.submitLabel }}
      </MudaButton>
      <slot name="actionsAfter" />
    </div>
  </form>
</template>
