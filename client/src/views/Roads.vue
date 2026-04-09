<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import api from "../api";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import Card from "primevue/card";
import Tag from "primevue/tag";
import Button from "primevue/button";
import InputText from "primevue/inputtext";
import IconField from "primevue/iconfield";
import InputIcon from "primevue/inputicon";
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

const congestion = ref(null);
const filter = ref("");
const loading = ref(true);

function statusSeverity(status) {
  if (status === "CONGESTED") return "danger";
  if (status === "HEAVY") return "warn";
  if (status === "NORMAL") return "info";
  return "success";
}

function coverageColor(pct) {
  if (pct > 55) return "#ef4444";
  if (pct > 35) return "#f97316";
  if (pct > 12) return "#eab308";
  return "#22c55e";
}

// Build per-road summary from grid intersections
const roads = computed(() => {
  if (!congestion.value?.intersections) return [];
  const roadMap = {};
  for (const item of congestion.value.intersections) {
    const road = INTERSECTION_ROADS[item.intersection] || "Unknown";
    if (!roadMap[road]) {
      roadMap[road] = { name: road, intersections: [] };
    }
    roadMap[road].intersections.push(item);
  }
  return Object.values(roadMap).map((r) => {
    const avg = r.intersections.reduce((a, i) => a + i.congestion, 0) / r.intersections.length;
    const peak = Math.max(...r.intersections.map((i) => i.congestion));
    let status;
    if (avg > 0.55) status = "CONGESTED";
    else if (avg > 0.35) status = "HEAVY";
    else if (avg > 0.12) status = "NORMAL";
    else status = "FREE_FLOW";
    return {
      name: r.name,
      congestion: avg,
      congestionPct: +(avg * 100).toFixed(1),
      peakPct: +(peak * 100).toFixed(1),
      status,
      intersectionCount: r.intersections.length,
      intersections: r.intersections.map((i) => ({
        name: DISPLAY_NAMES[i.intersection] || i.intersection,
        congestion: i.congestion,
        status: i.status,
      })),
    };
  });
});

async function load() {
  loading.value = true;
  try {
    const { data } = await api.get("/congestion/status");
    congestion.value = data;
  } finally {
    loading.value = false;
  }
}

let refreshInterval = null;
onMounted(() => {
  load();
  refreshInterval = setInterval(load, 30000);
});
onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval);
});
</script>

<template>
  <div class="container">
    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:1rem;">
      <div>
        <h1 class="page-title" style="margin:0;">Roads</h1>
        <p class="muted" style="margin:0;">Live traffic from grid analysis</p>
      </div>
      <Button icon="pi pi-refresh" label="Refresh" @click="load" :loading="loading" outlined />
    </div>

    <!-- Road summaries -->
    <div class="road-list">
      <Card v-for="road in roads" :key="road.name">
        <template #content>
          <div style="display:flex; justify-content:space-between; align-items:center; gap:1rem;">
            <div style="flex:1;">
              <div style="font-weight:600; font-size:1.05rem;">{{ road.name }}</div>
              <div style="display:flex; align-items:center; gap:.5rem; margin-top:.4rem;">
                <ProgressBar
                  :value="road.congestionPct"
                  :showValue="false"
                  style="height:8px; flex:1; max-width:160px;"
                  :pt="{ value: { style: { background: coverageColor(road.congestionPct) } } }"
                />
                <span class="muted" style="font-size:.8rem;">{{ road.congestionPct }}% avg</span>
                <span class="muted" style="font-size:.75rem;">(peak {{ road.peakPct }}%)</span>
              </div>
              <!-- Intersection breakdown -->
              <div style="margin-top:.5rem; display:flex; flex-wrap:wrap; gap:.4rem;">
                <div v-for="int in road.intersections" :key="int.name" class="int-chip">
                  <span style="font-size:.75rem;">{{ int.name }}</span>
                  <Tag :severity="statusSeverity(int.status)" :value="(int.congestion * 100).toFixed(0) + '%'" style="font-size:.65rem;" />
                </div>
              </div>
            </div>
            <Tag :severity="statusSeverity(road.status)" :value="road.status.replace('_', ' ')" style="font-size:.85rem;" />
          </div>
        </template>
      </Card>
    </div>
  </div>
</template>

<style scoped>
.road-list {
  display: flex;
  flex-direction: column;
  gap: .75rem;
}
.int-chip {
  display: flex;
  align-items: center;
  gap: .3rem;
  padding: .15rem .4rem;
  background: rgba(255,255,255,0.03);
  border-radius: 4px;
  border: 1px solid rgba(255,255,255,0.06);
}
</style>
