import { onScopeDispose, ref, type ShallowRef, shallowRef } from "vue";

export type AsyncCallState<TResult, TError> =
  | { readonly status: "idle" }
  | { readonly status: "loading"; readonly prevResult: TResult | undefined }
  | { readonly status: "success"; readonly result: TResult }
  | { readonly status: "failure"; readonly error: TError; readonly prevResult: TResult | undefined };

export interface AsyncCallContext {
  signal: AbortSignal;
}

export type AsyncCallFunc<TResult, TArgs extends unknown[]> = (
  ctx: AsyncCallContext,
  ...args: TArgs
) => Promise<TResult>;

export interface AsyncCallReturnType<TResult, TArgs extends unknown[], TError> {
  dispatch(...args: TArgs): Promise<TResult>;
  reset(): void;
  state: ShallowRef<AsyncCallState<TResult, TError>>;
}

export interface AsyncCallPollReturnType<TResult, TArgs extends unknown[], TError> {
  restart(...args: TArgs): Promise<void>;
  start(...args: TArgs): Promise<void>;
  state: ShallowRef<AsyncCallState<TResult, TError>>;
  stop(): void;
}

export type AsyncCallAllData<T> = {
  [K in keyof T]: T[K] extends Promise<infer R> ? R : never;
};

/**
 * Wraps an async operation in a reactive request state machine.
 *
 * The state moves through `idle`, `loading`, `success`, and `failure`,
 * preserving the last successful result across loading and failure so the UI
 * can keep rendering stale content. Concurrent dispatches are guarded by a
 * request id: only the most recent call may write the state, so late
 * responses from outdated requests are ignored.
 */
export function useAsyncCall<TResult = unknown, TArgs extends unknown[] = [], TError = unknown>(
  func: AsyncCallFunc<TResult, TArgs>,
  getDefaultValue?: () => TResult,
): AsyncCallReturnType<TResult, TArgs, TError> {
  const lastRequestId = ref(0);

  const state = shallowRef<AsyncCallState<TResult, TError>>(
    getDefaultValue != null ? { status: "success", result: getDefaultValue() } : { status: "idle" },
  );

  const abortController = ref<AbortController | null>(null);

  /** Returns the state to `idle` and invalidates any in-flight request. */
  const reset = () => {
    lastRequestId.value += 1;
    state.value = getDefaultValue != null ? { status: "success", result: getDefaultValue() } : { status: "idle" };

    if (abortController.value != null) {
      abortController.value.abort();
      abortController.value = null;
    }
  };

  /**
   * Runs the operation and updates the state with its outcome.
   *
   * Keeps the previous result visible while loading and after a failure, and
   * discards the outcome if a newer dispatch has started in the meantime.
   * Rejections are rethrown after the state is updated.
   */
  const dispatch = async (...args: TArgs): Promise<TResult> => {
    const requestId = ++lastRequestId.value;
    if (abortController.value != null) {
      abortController.value.abort();
      abortController.value = null;
    }
    const controller = new AbortController();
    abortController.value = controller;

    const prevResult =
      state.value.status === "success"
        ? state.value.result
        : state.value.status === "idle"
          ? undefined
          : state.value.prevResult;

    state.value = { status: "loading", prevResult };

    try {
      const result = await func({ signal: controller.signal }, ...args);
      if (!controller.signal.aborted && requestId === lastRequestId.value) {
        state.value = { status: "success", result };
      }
      return result;
    } catch (error) {
      if (!controller.signal.aborted && requestId === lastRequestId.value) {
        state.value = { status: "failure", error: error as TError, prevResult };
      }
      throw error;
    } finally {
      if (abortController.value === controller) {
        abortController.value = null;
      }
    }
  };

  onScopeDispose(() => {
    if (abortController.value != null) {
      abortController.value.abort();
      abortController.value = null;
    }
  });

  return {
    dispatch,
    reset,
    state,
  };
}

/**
 * Aggregates an object of request promises into a single response keyed by
 * the same properties. Resolves once every promise settles, or rejects as
 * soon as any request fails, so the result can be consumed by `useAsyncCall`
 * dispatchers.
 */
useAsyncCall.all = <T extends Record<PropertyKey, Promise<unknown>>>(input: T) => {
  return new Promise<AsyncCallAllData<T>>((resolve, reject) => {
    const data: Partial<AsyncCallAllData<T>> = {};

    let count = 0;

    const total = Object.keys(input).length;

    if (total === 0) {
      resolve(data as AsyncCallAllData<T>);
      return;
    }

    for (const key in input) {
      input[key]
        ?.then((response) => {
          data[key] = response as AsyncCallAllData<T>[typeof key];
          count += 1;

          if (count >= total) {
            resolve(data as AsyncCallAllData<T>);
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
useAsyncCall.poll = <TResult = unknown, TArgs extends unknown[] = [], TError = unknown>(
  func: AsyncCallFunc<TResult, TArgs>,
  ms: number,
): AsyncCallPollReturnType<TResult, TArgs, TError> => {
  const timerId = ref<number | null>(null);
  let pollingId = 0;
  let running = false;

  const { dispatch, reset, state } = useAsyncCall<TResult, TArgs, TError>(func);

  /** Dispatches once, then schedules the next tick after the request settles. */
  const poll = async (id: number, args: TArgs): Promise<void> => {
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
  const start = (...args: TArgs): Promise<void> => {
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
  const restart = (...args: TArgs): Promise<void> => {
    stop();
    return start(...args);
  };

  onScopeDispose(stop);

  return { start, stop, restart, state };
};
