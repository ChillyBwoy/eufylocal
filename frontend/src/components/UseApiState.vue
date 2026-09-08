<script setup lang="ts" generic="T">
import { computed } from "vue";

import { type UseApiState as ApiState } from "@/composables/useApi";

const props = defineProps<{
  state: ApiState<T>;
}>();

defineSlots<{
  idle(): unknown;
  loading(): unknown;
  failure(props: { error: unknown }): unknown;
  body(props: { result: T }): unknown;
}>();

const result = computed<T | undefined>(() => {
  if (props.state.status === "idle") {
    return undefined;
  }

  return props.state.status === "success" ? props.state.result : props.state.prevResult;
});
</script>

<template>
  <slot v-if="state.status === 'idle'" name="idle" />
  <slot v-else-if="state.status === 'loading' && result === undefined" name="loading" />
  <slot v-else-if="state.status === 'failure' && result === undefined" name="failure" :error="state.error" />
  <slot v-else name="body" :result="result!" />
</template>
