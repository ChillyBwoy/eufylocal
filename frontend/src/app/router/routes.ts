export type AppRoute = () => {
  path: string;
  name: string;
};

export const dashboard: AppRoute = () => ({
  name: "dashboard",
  path: "/",
});

export const users: AppRoute = () => ({
  name: "users",
  path: "/users",
});

export const routes = {
  dashboard,
  users,
} as const;
