import { defineStore } from "pinia";
import api from "../api";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: JSON.parse(localStorage.getItem("user") || "null"),
  }),
  getters: {
    isAuthenticated: (s) => !!s.user,
  },
  actions: {
    async signup(payload) {
      const { data } = await api.post("/auth/signup", payload);
      this.setUser(data.user);
    },
    async signin(payload) {
      const { data } = await api.post("/auth/signin", payload);
      this.setUser(data.user);
    },
    async signout() {
      try {
        await api.post("/auth/signout");
      } catch {}
      this.setUser(null);
    },
    setUser(user) {
      this.user = user;
      if (user) localStorage.setItem("user", JSON.stringify(user));
      else localStorage.removeItem("user");
    },
  },
});
