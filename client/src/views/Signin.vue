<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import Card from "primevue/card";
import InputText from "primevue/inputtext";
import Password from "primevue/password";
import Button from "primevue/button";
import Message from "primevue/message";

const email = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);
const auth = useAuthStore();
const router = useRouter();

async function submit() {
  error.value = "";
  loading.value = true;
  try {
    await auth.signin({ email: email.value, password: password.value });
    router.push("/dashboard");
  } catch (e) {
    error.value = e.response?.data?.error || "Sign in failed";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="auth-wrap">
    <div class="auth-layout">
      <div class="auth-intro">
        <div class="auth-eyebrow">Welcome Back</div>
        <h1 class="auth-title">Your metro awaits</h1>
        <p class="auth-subtitle">Real-time traffic & density monitoring powered by AI</p>
      </div>
      <Card class="auth-card">
          <template #title>
            <div class="brand">
              <img src="/logo.png" alt="EagleVision" class="brand-logo-img" />
              <span>Metro Density</span>
            </div>
          </template>
          <template #subtitle>Sign in to your account</template>
          <template #content>
            <form @submit.prevent="submit" class="stagger">
              <div>
                <label class="muted" for="email" style="font-size:.85rem; display:block; margin-bottom:.4rem;">Email</label>
                <InputText id="email" v-model="email" type="email" required fluid />
              </div>
              <div>
                <label class="muted" for="pw" style="font-size:.85rem; display:block; margin-bottom:.4rem;">Password</label>
                <Password id="pw" v-model="password" :feedback="false" toggleMask required fluid />
              </div>
              <Button type="submit" label="Sign in" icon="pi pi-sign-in" :loading="loading" />
              <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
            </form>
          </template>
          <template #footer>
            <span class="muted">No account? </span>
            <router-link to="/signup" style="color:var(--accent); font-weight:600; text-decoration:none;">Create one</router-link>
          </template>
      </Card>
    </div>
  </div>
</template>
