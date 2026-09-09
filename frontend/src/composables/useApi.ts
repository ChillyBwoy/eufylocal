import { onScopeDispose, type Ref, ref, type ShallowRef, shallowRef } from "vue";

export type UseApiState<T> =
  | { readonly status: "idle" }
  | { readonly status: "loading"; readonly prevResult: T | undefined }
  | { readonly status: "success"; readonly result: T }
  | { readonly status: "failure"; readonly error: unknown; readonly prevResult: T | undefined };

export interface UseApiResponse<T> {
  data: T;
}

export type UseApiOperation<T, A extends unknown[]> = (...args: A) => Promise<UseApiResponse<T>>;

export interface UseApiReturnType<T, TArgs extends unknown[]> {
  state: ShallowRef<UseApiState<T>>;
  dispatch(...args: TArgs): Promise<UseApiResponse<T>>;
  reset(): void;
}

export interface UseApiPollReturnType<T, TArgs extends unknown[]> {
  state: ShallowRef<UseApiState<T>>;
  start(...args: TArgs): Promise<void>;
  stop(): void;
  restart(...args: TArgs): Promise<void>;
}

/**
 * Wraps an async API operation in a reactive request state machine.
 *
 * The state moves through `idle`, `loading`, `success`, and `failure`,
 * preserving the last successful result across loading and failure so the UI
 * can keep rendering stale content. Concurrent dispatches are guarded by a
 * request id: only the most recent call may write the state, so late
 * responses from outdated requests are ignored.
 */
export function useApi<T = unknown, A extends unknown[] = [], E = unknown>(
  func: UseApiOperation<T, A>,
): UseApiReturnType<T, A> {
  const state: Ref<UseApiState<T>> = shallowRef({ status: "idle" });
  const lastRequestId = ref(0);

  /** Returns the state to `idle` and invalidates any in-flight request. */
  const reset = () => {
    lastRequestId.value += 1;
    state.value = { status: "idle" };
  };

  /**
   * Runs the operation and updates the state with its outcome.
   *
   * Keeps the previous result visible while loading and after a failure, and
   * discards the outcome if a newer dispatch has started in the meantime.
   * Rejections are rethrown after the state is updated.
   */
  const dispatch = async (...args: A): Promise<UseApiResponse<T>> => {
    const prevResult =
      state.value.status === "success"
        ? state.value.result
        : state.value.status === "idle"
          ? undefined
          : state.value.prevResult;
    state.value = {
      status: "loading",
      prevResult,
    };
    const requestId = lastRequestId.value + 1;
    lastRequestId.value = requestId;

    try {
      const response = await func(...args);
      if (requestId === lastRequestId.value) {
        state.value = { status: "success", result: response.data };
      }
      return response;
    } catch (error) {
      if (requestId === lastRequestId.value) {
        state.value = { status: "failure", error: error as E, prevResult };
      }
      throw error;
    }
  };

  return {
    dispatch,
    reset,
    state,
  };
}

export type UseApiAllRequest<T> = Promise<{ data: T }>;

export type UseApiAllData<T> = {
  [K in keyof T]: T[K] extends UseApiAllRequest<infer R> ? R : never;
};

/**
 * Aggregates an object of request promises into a single response keyed by
 * the same properties. Resolves once every promise settles, or rejects as
 * soon as any request fails, so the result can be consumed by `useApi`
 * dispatchers.
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

/**
 * Repeatedly dispatches the operation on a self-scheduling timer.
 *
 * The next tick is scheduled only after the current request settles, so
 * requests never overlap. Request errors are kept in the state but never
 * stop the loop. Polling stops automatically when the calling scope is
 * disposed.
 */
useApi.poll = <T = unknown, A extends unknown[] = [], E = unknown>(
  func: UseApiOperation<T, A>,
  ms: number,
): UseApiPollReturnType<T, A> => {
  const timerId = ref<number | null>(null);
  let pollingId = 0;
  let running = false;

  const { dispatch, reset, state } = useApi<T, A, E>(func);

  /** Dispatches once, then schedules the next tick after the request settles. */
  const poll = async (id: number, args: A): Promise<void> => {
    try {
      await dispatch(...args);
    } catch {
      // The request state contains the error; polling continues on the next interval.
    } finally {
      if (running && id === pollingId) {
        timerId.value = window.setTimeout(() => void poll(id, args), ms);
      }
    }
  };

  /** Starts polling with an immediate first dispatch. No-op if already running. */
  const start = (...args: A): Promise<void> => {
    if (running) {
      return Promise.resolve();
    }

    running = true;
    pollingId += 1;
    return poll(pollingId, args);
  };

  /** Stops polling, cancels the pending tick, and resets the state to `idle`. */
  const stop = () => {
    running = false;
    pollingId += 1;
    reset();
    if (timerId.value != null) {
      window.clearTimeout(timerId.value);
    }
    timerId.value = null;
  };

  /** Stops polling and immediately starts it again. */
  const restart = (...args: A): Promise<void> => {
    stop();
    return start(...args);
  };

  onScopeDispose(stop);

  return { start, stop, restart, state };
};
