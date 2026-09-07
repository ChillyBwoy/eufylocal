import { type Ref, ref, type ShallowRef, shallowRef } from "vue";

export type UseApiState<T> =
  | { readonly status: "idle" }
  | { readonly status: "loading" }
  | { readonly status: "success"; readonly result: T }
  | { readonly status: "failure"; readonly error: unknown };

export interface UseApiResponse<T> {
  data: T;
}

export type UseApiOperation<T, A extends unknown[]> = (...args: A) => Promise<UseApiResponse<T>>;

export type UseApiReturnType<T, TArgs extends unknown[]> = [
  (...args: TArgs) => Promise<UseApiResponse<T>>,
  ShallowRef<UseApiState<T>>,
  () => void,
];

export function useApi<T = unknown, A extends unknown[] = [], E = unknown>(
  func: UseApiOperation<T, A>,
): UseApiReturnType<T, A> {
  const state: Ref<UseApiState<T>> = shallowRef({ status: "idle" });
  const lastRequestId = ref(0);

  const reset = () => {
    lastRequestId.value += 1;
    state.value = { status: "idle" };
  };

  const handler = async (...args: A): Promise<UseApiResponse<T>> => {
    state.value = { status: "loading" };
    const requestId = lastRequestId.value + 1;
    lastRequestId.value = requestId;

    const response = await func(...args);
    if (requestId === lastRequestId.value) {
      state.value = { status: "success", result: response.data };
    }
    return response;
  };

  return [handler, state, reset];
}

export type UseApiAllRequest<T> = Promise<{ data: T }>;

export type UseApiAllData<T> = {
  [K in keyof T]: T[K] extends UseApiAllRequest<infer R> ? R : never;
};

/**
 * This function mimics AxiosResponse
 */
useApi.all = <T extends Record<PropertyKey, UseApiAllRequest<unknown>>>(input: T) => {
  return new Promise<UseApiResponse<UseApiAllData<T>>>((resolve, reject) => {
    const data: Partial<UseApiAllData<T>> = {};

    let count = 0;

    const total = Object.keys(input).length;

    for (const key in input) {
      input[key]
        ?.then((response) => {
          data[key] = response.data as UseApiAllData<T>[typeof key];
          count += 1;

          if (count >= total) {
            const response: UseApiResponse<UseApiAllData<T>> = {
              data: data as UseApiAllData<T>,
            };
            resolve(response);
          }
        })
        .catch(reject);
    }
  });
};
