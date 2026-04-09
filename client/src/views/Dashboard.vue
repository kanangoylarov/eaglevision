<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import api from "../api";
import Card from "primevue/card";
import Tag from "primevue/tag";
import ProgressSpinner from "primevue/progressspinner";
import ProgressBar from "primevue/progressbar";

const DISPLAY_NAMES = {
  "Neftchilar/Nizami": "Sahil area",
  "Neftchilar/H.Aliyev": "Bayil road",
  "Neftchilar/Heydar": "Boulevard",
  "Babek/Nizami": "Memar Ajami",
  "Babek/H.Aliyev": "Old City area",
  "Babek/Heydar": "Hazi Aslanov rd.",
  "Tbilisi/Nizami": "20 January area",
  "Tbilisi/H.Aliyev": "Narimanov area",
  "Bunyadov/Nizami": "Koroglu area",
  "Bunyadov/H.Aliyev": "Gara Garayev area",
  "Bunyadov/Heydar": "Hazi Aslanov m.",
};

const ROAD_NAMES = {
  "Neftchilar Ave": "Neftchilar Ave",
  "Babek Ave": "Babek Ave",
  "Tbilisi Ave": "Tbilisi Ave",
  "Z.Bunyadov Ave": "Z.Bunyadov Ave",
  "Nizami St": "M.Mushfig St",
  "H.Aliyev St": "A.Aliyev St",
  "Heydar Aliyev Ave": "H.Aliyev Ave",
};

// Which road each intersection sits on (primary road)
const INTERSECTION_ROADS = {
  "Neftchilar/Nizami": "Neftchilar Ave",
  "Neftchilar/H.Aliyev": "Neftchilar Ave",
  "Neftchilar/Heydar": "Neftchilar Ave",
  "Babek/Nizami": "Babek Ave",
  "Babek/H.Aliyev": "Babek Ave",
  "Babek/Heydar": "Babek Ave",
  "Tbilisi/Nizami": "Tbilisi Ave",
  "Tbilisi/H.Aliyev": "Tbilisi Ave",
  "Bunyadov/Nizami": "Z.Bunyadov Ave",
  "Bunyadov/H.Aliyev": "Z.Bunyadov Ave",
  "Bunyadov/Heydar": "Z.Bunyadov Ave",
};

const trains = ref([]);
const stations = ref([]);
const congestion = ref(null);
const loading = ref(true);

async function loadAll() {
  try {
    const [t, s, c] = await Promise.all([
      api.get("/trains"),
      api.get("/stations"),
      api.get("/congestion/status"),
    ]);
    trains.value = t.data;
    stations.value = s.data;
    congestion.value = c.data;
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

const totalPeople = computed(() =>
  stations.value.reduce((acc, s) => acc + (s.humanCount || 0), 0)
);
const highDensityStations = computed(() =>
  stations.value.filter((s) => (s.aiResult || "").includes("high")).length
);

// Aggregate intersections into road-level summaries
const roadSummaries = computed(() => {
  if (!congestion.value?.intersections) return [];
  const roadMap = {};
  for (const item of congestion.value.intersections) {
    const road = INTERSECTION_ROADS[item.intersection] || "Unknown";
    if (!roadMap[road]) {
      roadMap[road] = { name: ROAD_NAMES[road] || road, values: [], statuses: [] };
    }
    roadMap[road].values.push(item.congestion);
    roadMap[road].statuses.push(item.status);
  }
  return Object.values(roadMap).map((r) => {
    const avg = r.values.reduce((a, b) => a + b, 0) / r.values.length;
    let status;
    if (avg > 0.55) status = "CONGESTED";
    else if (avg > 0.35) status = "HEAVY";
    else if (avg > 0.12) status = "NORMAL";
    else status = "FREE_FLOW";
    return { name: r.name, congestion: avg, status };
  });
});

const congestedRoadCount = computed(() =>
  roadSummaries.value.filter((r) => r.status === "CONGESTED" || r.status === "HEAVY").length
);

const totalIntersections = computed(() =>
  congestion.value?.intersections?.length || 0
);

function statusSeverity(status) {
  if (status === "CONGESTED") return "danger";
  if (status === "HEAVY") return "warn";
  if (status === "NORMAL") return "info";
  return "success";
}

function densitySeverity(ai) {
  if (!ai) return "secondary";
  if (ai.includes("high")) return "danger";
  if (ai.includes("medium")) return "warn";
  return "success";
}

function coverageColor(c) {
  if (c > 55) return "#ef4444";
  if (c > 35) return "#f97316";
  if (c > 12) return "#eab308";
  return "#22c55e";
}
</script>

<template>
  <div class="container">
    <h1 class="page-title">Dashboard</h1>
    <p class="muted" style="margin-top:-.5rem;">Real-time metro & traffic monitoring</p>

    <div v-if="loading" style="display:grid; place-items:center; padding:3rem;">
      <ProgressSpinner />
    </div>

    <div v-else>
      <!-- Stats -->
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
              <div class="value" style="color:#a78bfa;">{{ totalIntersections }}</div>
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
              <div class="value" style="color:#fb923c;">{{ roadSummaries.length }}</div>
              <div class="label"><i class="pi pi-car" /> Roads Tracked</div>
            </div>
          </template>
        </Card>
      </div>

      <!-- Alerts row -->
      <div class="grid cols-2" style="margin-top:1rem;">
        <Card>
          <template #content>
            <div class="stat">
              <div class="value" style="color:#f87171;">{{ highDensityStations }}</div>
              <div class="label"><i class="pi pi-exclamation-triangle" /> High Density Stations</div>
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

      <!-- Live road status from grid -->
      <h2 style="margin-top:2rem; font-size:1.2rem;">Road Status (Live)</h2>
      <div class="road-list">
        <Card v-for="road in roadSummaries" :key="road.name" class="road-card">
          <template #content>
            <div style="display:flex; justify-content:space-between; align-items:center; gap:1rem;">
              <div style="flex:1; min-width:0;">
                <div style="font-weight:600;">{{ road.name }}</div>
                <div style="display:flex; align-items:center; gap:.5rem; margin-top:.4rem;">
                  <ProgressBar
                    :value="road.congestion * 100"
                    :showValue="false"
                    style="height:6px; flex:1; max-width:140px;"
                    :pt="{ value: { style: { background: coverageColor(road.congestion * 100) } } }"
                  />
                  <span class="muted" style="font-size:.75rem;">{{ (road.congestion * 100).toFixed(1) }}%</span>
                </div>
              </div>
              <Tag :severity="statusSeverity(road.status)" :value="road.status.replace('_', ' ')" />
            </div>
          </template>
        </Card>
      </div>

      <!-- Intersection detail -->
      <h2 style="margin-top:2rem; font-size:1.2rem;">Intersections</h2>
      <div class="station-grid" v-if="congestion">
        <Card v-for="item in congestion.intersections" :key="item.intersection">
          <template #content>
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span style="font-weight:500; font-size:.9rem;">{{ DISPLAY_NAMES[item.intersection] || item.intersection }}</span>
              <div style="display:flex; align-items:center; gap:.3rem;">
                <span class="muted" style="font-size:.75rem;">{{ (item.congestion * 100).toFixed(0) }}%</span>
                <Tag :severity="statusSeverity(item.status)" :value="item.status.replace('_',' ')" style="font-size:.7rem;" />
              </div>
            </div>
          </template>
        </Card>
      </div>

      <!-- Metro stations quick view -->
      <h2 style="margin-top:2rem; font-size:1.2rem;">Metro Stations</h2>
      <div class="station-grid">
        <Card v-for="station in stations" :key="station.id" class="station-chip">
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
.road-list {
  display: flex;
  flex-direction: column;
  gap: .5rem;
}
.station-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: .5rem;
}
</style>
