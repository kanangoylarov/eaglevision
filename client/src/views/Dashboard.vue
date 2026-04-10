<script setup>
import { ref, computed, onMounted } from "vue";
import api from "../api";
import Card from "primevue/card";
import ProgressSpinner from "primevue/progressspinner";

const trains = ref([]);
const stations = ref([]);
const loading = ref(true);

onMounted(async () => {
  try {
    const [t, s] = await Promise.all([api.get("/trains"), api.get("/stations")]);
    trains.value = t.data;
    stations.value = s.data;
  } finally {
    loading.value = false;
  }
});

const totalPeople = computed(() =>
  trains.value.reduce((acc, t) => acc + (t.humanCount || 0), 0)
);
const highDensity = computed(() =>
  trains.value.filter((t) => (t.aiResult || "").includes("high")).length
);
</script>

<template>
  <div class="container">
    <h1 class="page-title">Dashboard</h1>
    <p class="muted" style="margin-top:-.5rem;">EagleVision — AI crowd density monitoring</p>

    <div v-if="loading" style="display:grid; place-items:center; padding:3rem;">
      <ProgressSpinner />
    </div>

    <div v-else class="grid cols-3" style="margin-top:1.5rem;">
      <Card>
        <template #content>
          <div class="stat">
            <div class="value" style="color:#0ea5e9;">{{ stations.length }}</div>
            <div class="label"><i class="pi pi-map-marker" /> Stations</div>
          </div>
        </template>
      </Card>
      <Card>
        <template #content>
          <div class="stat">
            <div class="value" style="color:#a78bfa;">{{ trains.length }}</div>
            <div class="label"><i class="pi pi-bolt" /> Active Trains</div>
          </div>
        </template>
      </Card>
      <Card>
        <template #content>
          <div class="stat">
            <div class="value" style="color:#34d399;">{{ totalPeople }}</div>
            <div class="label"><i class="pi pi-users" /> People Detected</div>
          </div>
        </template>
      </Card>
      <Card>
        <template #content>
          <div class="stat">
            <div class="value" style="color:#f87171;">{{ highDensity }}</div>
            <div class="label"><i class="pi pi-exclamation-triangle" /> High Density</div>
          </div>
        </template>
      </Card>
    </div>
  </div>
</template>
