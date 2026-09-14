import "@/assets/app.css";
import "@mudakit/ui/style.css";

import { createApp } from "vue";

import App from "@/app/App.vue";
import router from "@/app/router/index.ts";

const app = createApp(App);
app.use(router);
app.mount("#app");
