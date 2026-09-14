import { computed, readonly, ref, watch } from "vue";

export type Theme = "light" | "dark";

const STORAGE_KEY = "eufylocal:theme";

function isTheme(value: string | null): value is Theme {
  return value === "light" || value === "dark";
}

export function useTheme() {
  const storedTheme = window.localStorage.getItem(STORAGE_KEY);
  const systemTheme: Theme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  const theme = ref<Theme>(isTheme(storedTheme) ? storedTheme : systemTheme);

  watch(
    theme,
    (value) => {
      document.documentElement.dataset.theme = value;
      document.documentElement.style.colorScheme = value;
      window.localStorage.setItem(STORAGE_KEY, value);
    },
    { flush: "sync", immediate: true },
  );

  function setTheme(value: Theme): void {
    theme.value = value;
  }

  function toggleTheme(): void {
    setTheme(theme.value === "dark" ? "light" : "dark");
  }

  return {
    isDark: computed(() => theme.value === "dark"),
    setTheme,
    theme: readonly(theme),
    toggleTheme,
  };
}
