<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import api from "../api";
import Card from "primevue/card";
import Tag from "primevue/tag";
import ProgressSpinner from "primevue/progressspinner";
import ProgressBar from "primevue/progressbar";

const NODE_ROADS = {
  neft_nizami: "Neftchilar Ave", neft_aliyev: "Neftchilar Ave", neft_heydar: "Neftchilar Ave",
  babek_nizami: "Babek Ave", babek_aliyev: "Babek Ave", babek_heydar: "Babek Ave",
  tbilisi_nizami: "Tbilisi Ave", tbilisi_aliyev: "Tbilisi Ave",
  bunyadov_nizami: "Z.Bunyadov Ave", bunyadov_aliyev: "Z.Bunyadov Ave", bunyadov_heydar: "Z.Bunyadov Ave",
};

const trains = ref([]);
const stations = ref([]);
const navStatus = ref(null);
const loading = ref(true);

async function loadAll() {
  try {
    const [t, s, n] = await Promise.all([
      api.get("/trains"),
      api.get("/stations"),
      api.get("/nav/status"),
    ]);
    trains.value = t.data;
    stations.value = s.data;
    navStatus.value = n.data;
  } finally {
    loading.value = false;
  }
}

let refreshInterval = null;
onMounted(() => {
  loadAll();
  refreshInterval = setInterval(loadAll, 30000);
});
onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval);
});

const roadNodes = computed(() =>
  (navStatus.value?.nodes || []).filter((n) => n.mode === "road")
);

const totalPeople = computed(() =>
  stations.value.reduce((acc, s) => acc + (s.humanCount || 0), 0)
);
const highDensityStations = computed(() =>
  stations.value.filter((s) => (s.aiResult || "").includes("high")).length
);

const roadSummaries = computed(() => {
  const roadMap = {};
  for (const node of roadNodes.value) {
    const road = NODE_ROADS[node.node_id] || "Unknown";
    if (!roadMap[road]) roadMap[road] = { name: road, nodes: [] };
    roadMap[road].nodes.push(node);
  }
  return Object.values(roadMap).map((r) => {
    const avgForecast = r.nodes.reduce((a, n) => a + n.forecast_1h, 0) / r.nodes.length;
    let status;
    if (avgForecast > 70) status = "CONGESTED";
    else if (avgForecast > 50) status = "HEAVY";
    else if (avgForecast > 25) status = "NORMAL";
    else status = "FREE_FLOW";
    return { name: r.name, forecast: avgForecast, status, nodes: r.nodes };
  });
});

const congestedRoadCount = computed(() =>
  roadSummaries.value.filter((r) => r.status === "CONGESTED" || r.status === "HEAVY").length
);

function statusSeverity(s) {
  if (s === "CONGESTED") return "danger";
  if (s === "HEAVY") return "warn";
  if (s === "NORMAL") return "info";
  return "success";
}

function densitySeverity(ai) {
  if (!ai) return "secondary";
  if (ai.includes("high")) return "danger";
  if (ai.includes("medium")) return "warn";
  return "success";
}

function forecastColor(pct) {
  if (pct > 70) return "#ef4444";
  if (pct > 50) return "#f97316";
  if (pct > 25) return "#eab308";
  return "#22c55e";
}
</script>

<template>
  <div class="container">
    <h1 class="page-title">Dashboard</h1>
    <p class="muted" style="margin-top:-.5rem;">Real-time metro & traffic monitoring (LightGBM powered)</p>

    <div v-if="loading" style="display:grid; place-items:center; padding:3rem;">
      <ProgressSpinner />
    </div>

    <div v-else>
      <div class="grid cols-4" style="margin-top:1.5rem;">
        <Card>
          <template #content>
            <div class="stat">
              <div class="value" style="color:#0ea5e9;">{{ stations.length }}</div>
              <div class="label"><i class="pi pi-map-marker" /> Metro Stations</div>
            </div>
          </template>
        </Card>
        <Card>
          <template #content>
            <div class="stat">
              <div class="value" style="color:#a78bfa;">{{ roadNodes.length }}</div>
              <div class="label"><i class="pi pi-car" /> Intersections Monitored</div>
            </div>
          </template>
        </Card>
        <Card>
          <template #content>
            <div class="stat">
              <div class="value" style="color:#34d399;">{{ totalPeople }}</div>
              <div class="label"><i class="pi pi-users" /> People in Metro</div>
            </div>
          </template>
        </Card>
        <Card>
          <template #content>
            <div class="stat">
              <div class="value" style="color:#f87171;">{{ congestedRoadCount }}</div>
              <div class="label"><i class="pi pi-exclamation-triangle" /> Congested Roads</div>
            </div>
          </template>
        </Card>
      </div>

      <!-- Road status from LightGBM -->
      <h2 style="margin-top:2rem; font-size:1.2rem;">Road Status (AI Forecast)</h2>
      <div class="road-list">
        <Card v-for="road in roadSummaries" :key="road.name">
          <template #content>
            <div style="display:flex; justify-content:space-between; align-items:center; gap:1rem;">
              <div style="flex:1;">
                <div style="font-weight:600;">{{ road.name }}</div>
                <div style="display:flex; align-items:center; gap:.5rem; margin-top:.4rem;">
                  <ProgressBar
                    :value="road.forecast"
                    :showValue="false"
                    style="height:8px; flex:1; max-width:140px;"
                    :pt="{ value: { style: { background: forecastColor(road.forecast) } } }"
                  />
                  <span class="muted" style="font-size:.75rem;">{{ road.forecast.toFixed(1) }}%</span>
                </div>
              </div>
              <Tag :severity="statusSeverity(road.status)" :value="road.status.replace('_', ' ')" />
            </div>
          </template>
        </Card>
      </div>

      <!-- Per-intersection detail -->
      <h2 style="margin-top:2rem; font-size:1.2rem;">Intersections</h2>
      <div class="station-grid">
        <Card v-for="node in roadNodes" :key="node.node_id">
          <template #content>
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <div>
                <span style="font-weight:500; font-size:.9rem;">{{ node.name }}</span>
                <div class="muted" style="font-size:.7rem;">
                  {{ node.trend === 'increasing' ? '↑ increasing' : node.trend === 'decreasing' ? '↓ decreasing' : '→ stable' }}
                </div>
              </div>
              <div style="display:flex; align-items:center; gap:.3rem;">
                <span class="muted" style="font-size:.75rem;">{{ node.forecast_1h }}%</span>
                <Tag :severity="statusSeverity(node.status)" :value="node.status.replace('_',' ')" style="font-size:.7rem;" />
              </div>
            </div>
          </template>
        </Card>
      </div>

      <!-- Metro stations -->
      <h2 style="margin-top:2rem; font-size:1.2rem;">Metro Stations</h2>
      <div class="station-grid">
        <Card v-for="station in stations" :key="station.id">
          <template #content>
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span style="font-weight:500;">{{ station.name }}</span>
              <Tag v-if="station.aiResult" :severity="densitySeverity(station.aiResult)" :value="station.humanCount + ' ppl'" style="font-size:.75rem;" />
            </div>
          </template>
        </Card>
      </div>
    </div>
  </div>
</template>

<style scoped>
.road-list { display: flex; flex-direction: column; gap: .5rem; }
.station-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: .5rem; }
</style>
