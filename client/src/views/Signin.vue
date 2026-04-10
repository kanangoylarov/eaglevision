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
    <Card class="auth-card">
      <template #title>
        <div class="brand">
          <img src="/eagle.png" alt="EagleVision" class="brand-logo-img" />
          <span>EagleVision</span>
        </div>
      </template>
      <template #subtitle>Sign in to your account</template>
      <template #content>
        <form @submit.prevent="submit" style="display:flex; flex-direction:column; gap:1rem;">
          <div>
            <label class="muted" for="email">Email</label>
            <InputText id="email" v-model="email" type="email" required fluid />
          </div>
          <div>
            <label class="muted" for="pw">Password</label>
            <Password id="pw" v-model="password" :feedback="false" toggleMask required fluid />
          </div>
          <Button type="submit" label="Sign in" icon="pi pi-sign-in" :loading="loading" />
          <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
        </form>
      </template>
      <template #footer>
        <span class="muted">No account? </span>
        <router-link to="/signup">Create one</router-link>
      </template>
    </Card>
  </div>
</template>
