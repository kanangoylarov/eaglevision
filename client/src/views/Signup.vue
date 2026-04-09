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
  <div class="auth-wrap">
    <div class="auth-layout">
      <div class="auth-intro">
        <div class="auth-eyebrow">Get Started</div>
        <h1 class="auth-title">Join the movement</h1>
        <p class="auth-subtitle">Smart transportation insights at your fingertips</p>
      </div>
      <Card class="auth-card">
          <template #title>
            <div class="brand">
              <img src="/logo.png" alt="EagleVision" class="brand-logo-img" />
              <span>Metro Density</span>
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
</template>
