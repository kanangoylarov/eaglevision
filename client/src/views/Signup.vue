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
    <Card class="auth-card">
      <template #title>
        <div class="brand" style="justify-content:center;">
          <img src="/logo.jpeg" alt="EagleVision" class="brand-logo-img" style="width:48px;height:48px;" />
          <span>EagleVision</span>
        </div>
      </template>
      <template #subtitle>Create your account</template>
      <template #content>
        <form @submit.prevent="submit" style="display:flex; flex-direction:column; gap:1rem;">
          <div class="grid cols-2">
            <div>
              <label class="muted">First name</label>
              <InputText v-model="firstName" required fluid />
            </div>
            <div>
              <label class="muted">Last name</label>
              <InputText v-model="lastName" required fluid />
            </div>
          </div>
          <div>
            <label class="muted">Email</label>
            <InputText v-model="email" type="email" required fluid />
          </div>
          <div>
            <label class="muted">Password</label>
            <Password v-model="password" toggleMask required fluid />
          </div>
          <Button type="submit" label="Create account" icon="pi pi-user-plus" :loading="loading" />
          <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
        </form>
      </template>
      <template #footer>
        <span class="muted">Already have an account? </span>
        <router-link to="/signin">Sign in</router-link>
      </template>
    </Card>
  </div>
</template>
