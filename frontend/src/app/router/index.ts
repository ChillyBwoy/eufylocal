import { createRouter, createWebHistory } from "vue-router";

import { routes } from "./routes";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      ...routes.dashboard(),
      component: () => import("@/app/views/DashboardView.vue"),
    },
    {
      ...routes.users(),
      component: () => import("@/app/views/UsersView.vue"),
    },
  ],
});

export default router;
