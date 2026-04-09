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
  <div class="auth-wrap" style="min-height:100dvh; display:grid; place-items:center; padding:1rem;">
    <div style="width:100%; max-width:900px;">
      <div style="display:grid; grid-template-columns:1fr; gap:2rem; align-items:start;">
        <div class="auth-intro" style="color:var(--text);">
          <div style="font-size:.95rem; font-weight:600; color:var(--accent); margin-bottom:.5rem; letter-spacing:0.025em; text-transform:uppercase;">Welcome Back</div>
          <h1 style="font-family:'Manrope', sans-serif; font-size:2.5rem; font-weight:800; margin:0 0 .5rem 0; letter-spacing:-0.025em; line-height:1.1;">Your metro awaits</h1>
          <p style="font-size:1.125rem; color:var(--muted); margin:0; line-height:1.6;">Real-time traffic & density monitoring powered by AI</p>
        </div>
        <Card class="auth-card" style="max-width:420px; justify-self:start; width:100%;">
          <template #title>
            <div class="brand">
              <div class="brand-logo">M</div>
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
  </div>
</template>
