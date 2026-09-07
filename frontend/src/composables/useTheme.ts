import { computed, ref } from "vue";

export type Theme = "light" | "dark";

const STORAGE_KEY = "eufylocal:theme";

function readInitialTheme(): Theme {
  return document.documentElement.dataset.theme === "dark" ? "dark" : "light";
}

const theme = ref<Theme>(readInitialTheme());

function applyTheme(value: Theme): void {
  const root = document.documentElement;
  root.setAttribute("data-theme", value);
  root.style.colorScheme = value;
}

function setTheme(value: Theme): void {
  theme.value = value;
  window.localStorage.setItem(STORAGE_KEY, value);
  applyTheme(value);
}

function toggleTheme(): void {
  setTheme(theme.value === "dark" ? "light" : "dark");
}

export function useTheme() {
  return {
    theme: computed(() => theme.value),
    isDark: computed(() => theme.value === "dark"),
    setTheme,
    toggleTheme,
  };
}
