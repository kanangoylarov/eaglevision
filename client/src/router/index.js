import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";
import Signin from "../views/Signin.vue";
import Signup from "../views/Signup.vue";
import Dashboard from "../views/Dashboard.vue";
import Stations from "../views/Stations.vue";
import Trains from "../views/Trains.vue";
import Analyze from "../views/Analyze.vue";

const routes = [
  { path: "/", redirect: "/dashboard" },
  { path: "/signin", component: Signin, meta: { guest: true } },
  { path: "/signup", component: Signup, meta: { guest: true } },
  { path: "/dashboard", component: Dashboard, meta: { auth: true } },
  { path: "/stations", component: Stations, meta: { auth: true } },
  { path: "/trains", component: Trains, meta: { auth: true } },
  { path: "/analyze", component: Analyze, meta: { auth: true, admin: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  const auth = useAuthStore();
  if (to.meta.auth && !auth.isAuthenticated) return "/signin";
  if (to.meta.guest && auth.isAuthenticated) return "/dashboard";
  if (to.meta.admin && !auth.user?.isAdmin) return "/dashboard";
});

export default router;
