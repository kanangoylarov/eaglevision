<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import Card from "primevue/card";
import InputText from "primevue/inputtext";
import Password from "primevue/password";
import Button from "primevue/button";
import Message from "primevue/message";

const firstName = ref("");
const lastName = ref("");
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
    await auth.signup({
      firstName: firstName.value,
      lastName: lastName.value,
      email: email.value,
      password: password.value,
    });
    router.push("/dashboard");
  } catch (e) {
    error.value = e.response?.data?.error || "Sign up failed";
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
          <div style="font-size:.95rem; font-weight:600; color:var(--accent); margin-bottom:.5rem; letter-spacing:0.025em; text-transform:uppercase;">Get Started</div>
          <h1 style="font-family:'Manrope', sans-serif; font-size:2.5rem; font-weight:800; margin:0 0 .5rem 0; letter-spacing:-0.025em; line-height:1.1;">Join the movement</h1>
          <p style="font-size:1.125rem; color:var(--muted); margin:0; line-height:1.6;">Smart transportation insights at your fingertips</p>
        </div>
        <Card class="auth-card" style="max-width:420px; justify-self:start; width:100%;">
          <template #title>
            <div class="brand" style="justify-content:center;">
              <img src="/logo.jpeg" alt="EagleVision" class="brand-logo-img" style="width:48px;height:48px;" />
              <span>EagleVision</span>
            </div>
          </template>
          <template #subtitle>Create your account</template>
          <template #content>
            <form @submit.prevent="submit" class="stagger">
              <div class="grid cols-2">
                <div>
                  <label class="muted" style="font-size:.85rem; display:block; margin-bottom:.4rem;">First name</label>
                  <InputText v-model="firstName" required fluid />
                </div>
                <div>
                  <label class="muted" style="font-size:.85rem; display:block; margin-bottom:.4rem;">Last name</label>
                  <InputText v-model="lastName" required fluid />
                </div>
              </div>
              <div>
                <label class="muted" style="font-size:.85rem; display:block; margin-bottom:.4rem;">Email</label>
                <InputText v-model="email" type="email" required fluid />
              </div>
              <div>
                <label class="muted" style="font-size:.85rem; display:block; margin-bottom:.4rem;">Password</label>
                <Password v-model="password" toggleMask required fluid />
              </div>
              <Button type="submit" label="Create account" icon="pi pi-user-plus" :loading="loading" />
              <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
            </form>
          </template>
          <template #footer>
            <span class="muted">Already have an account? </span>
            <router-link to="/signin" style="color:var(--accent); font-weight:600; text-decoration:none;">Sign in</router-link>
          </template>
        </Card>
      </div>
    </div>
  </div>
</template>
