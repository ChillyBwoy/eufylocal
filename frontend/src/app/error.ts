import { get, set } from "lodash-es";

import type { HttpValidationError } from "@/api";

export interface AppFormError {
  type: string;
  message: string;
}

export type AppFormErrors<T> = T extends object
  ? { [K in keyof T]?: AppFormErrors<T[K]> }
  : T extends string | number | boolean | Array<unknown>
    ? Array<AppFormError>
    : never;

interface APIError {
  detail: string;
}

export const isAPIValidationError = (error: unknown): error is HttpValidationError => {
  return error != null && typeof error === "object" && "detail" in error && Array.isArray(error.detail);
};

export const isAPIPlainError = (error: unknown): error is APIError => {
  return error != null && typeof error === "object" && "detail" in error && typeof error.detail === "string";
};

export function mapFormValidationErrors<T>(error: HttpValidationError): Partial<AppFormErrors<T>> {
  const result: Partial<AppFormErrors<T>> = {};

  for (const err of error.detail ?? []) {
    const [, ...path] = err.loc;

    const existingErrors = get(result, path) ?? [];
    set(result, err.loc.slice(1), [
      ...existingErrors,
      {
        message: err.msg,
        type: err.type,
      },
    ]);
  }

  return result;
}
