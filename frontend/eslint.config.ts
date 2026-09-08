import skipFormatting from "@vue/eslint-config-prettier/skip-formatting";
import { defineConfigWithVueTs, vueTsConfigs } from "@vue/eslint-config-typescript";
import simpleImportSort from "eslint-plugin-simple-import-sort";
import pluginVue from "eslint-plugin-vue";

export default defineConfigWithVueTs(
  {
    plugins: {
      "simple-import-sort": simpleImportSort,
    },
  },
  {
    name: "files-to-lint",
    files: ["**/*.{ts,vue}"],
  },
  {
    ignores: ["node_modules/**", ".env", ".env.*", "package-lock.json", "**/locales/*", "src/api/**/*"],
  },
  pluginVue.configs["flat/essential"],
  vueTsConfigs.recommended,
  skipFormatting,
  {
    files: ["**/*.vue", "**/*.ts"],
    rules: {
      "no-unused-vars": "off",
      "@typescript-eslint/no-unused-vars": [
        "error",
        {
          argsIgnorePattern: "^_",
        },
      ],
      "simple-import-sort/imports": "error",
      "simple-import-sort/exports": "error",
      "sort-imports": "off",
    },
  },
);
