<script setup>
import { computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "./stores/auth";
import Menubar from "primevue/menubar";
import Button from "primevue/button";
import Toast from "primevue/toast";

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();

const items = computed(() => {
  const base = [
    { label: "Dashboard", icon: "pi pi-compass", command: () => router.push("/dashboard") },
    { label: "Metro", icon: "pi pi-map-marker", command: () => router.push("/metro") },
    { label: "Roads", icon: "pi pi-car", command: () => router.push("/roads") },
    { label: "Navigate", icon: "pi pi-directions", command: () => router.push("/navigation") },
  ];
  if (auth.user?.isAdmin) {
    base.push({ label: "Analyze", icon: "pi pi-camera", command: () => router.push("/analyze") });
  }
  return base;
});

async function logout() {
  await auth.signout();
  router.push("/signin");
}

const isAuthPage = computed(() => ["/signin", "/signup"].includes(route.path));
</script>

<template>
  <div class="app-shell dark">
    <Menubar v-if="auth.isAuthenticated && !isAuthPage" :model="items" class="border-noround">
      <template #start>
        <div class="brand" style="margin-right: 1rem;">
          <img src="/logo.jpeg" alt="EagleVision" class="brand-logo-img" />
          <span class="hidden md:inline">EagleVision</span>
        </div>
      </template>
      <template #end>
        <div style="display:flex; align-items:center; gap:.5rem;">
          <span class="muted" style="font-size:.85rem;" v-if="auth.user">
            {{ auth.user.firstName }}
          </span>
          <Button icon="pi pi-sign-out" text rounded severity="secondary" @click="logout" aria-label="Sign out" />
        </div>
      </template>
    </Menubar>

    <main style="flex:1;">
      <router-view />
    </main>

    <Toast position="top-right" />
  </div>
</template>
