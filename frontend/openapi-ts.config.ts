import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  input: {
    path: "../openapi.json",
  },
  output: {
    path: "src/api",
    postProcess: ["prettier"],
  },
});
