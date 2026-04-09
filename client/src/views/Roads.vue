<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import api from "../api";
import Card from "primevue/card";
import Tag from "primevue/tag";
import Button from "primevue/button";
import ProgressBar from "primevue/progressbar";

const DISPLAY_NAMES = {
  neft_nizami: "Sahil area", neft_aliyev: "Bayil road", neft_heydar: "Boulevard",
  babek_nizami: "Memar Ajami", babek_aliyev: "Old City area", babek_heydar: "Hazi Aslanov rd.",
  tbilisi_nizami: "20 January area", tbilisi_aliyev: "Narimanov area",
  bunyadov_nizami: "Koroglu area", bunyadov_aliyev: "Gara Garayev area", bunyadov_heydar: "Hazi Aslanov m.",
};

const NODE_ROADS = {
  neft_nizami: "Neftchilar Ave", neft_aliyev: "Neftchilar Ave", neft_heydar: "Neftchilar Ave",
  babek_nizami: "Babek Ave", babek_aliyev: "Babek Ave", babek_heydar: "Babek Ave",
  tbilisi_nizami: "Tbilisi Ave", tbilisi_aliyev: "Tbilisi Ave",
  bunyadov_nizami: "Z.Bunyadov Ave", bunyadov_aliyev: "Z.Bunyadov Ave", bunyadov_heydar: "Z.Bunyadov Ave",
};

const navStatus = ref(null);
const loading = ref(true);

function statusSeverity(s) {
  if (s === "CONGESTED") return "danger";
  if (s === "HEAVY") return "warn";
  if (s === "NORMAL") return "info";
  return "success";
}

function forecastColor(pct) {
  if (pct > 70) return "#ef4444";
  if (pct > 50) return "#f97316";
  if (pct > 25) return "#eab308";
  return "#22c55e";
}

const roads = computed(() => {
  if (!navStatus.value?.nodes) return [];
  const roadMap = {};
  for (const node of navStatus.value.nodes) {
    if (node.mode !== "road") continue;
    const road = NODE_ROADS[node.node_id] || "Unknown";
    if (!roadMap[road]) roadMap[road] = { name: road, nodes: [] };
    roadMap[road].nodes.push(node);
  }
  return Object.values(roadMap).map((r) => {
    const avg = r.nodes.reduce((a, n) => a + n.forecast_1h, 0) / r.nodes.length;
    const peak = Math.max(...r.nodes.map((n) => n.forecast_1h));
    let status;
    if (avg > 70) status = "CONGESTED";
    else if (avg > 50) status = "HEAVY";
    else if (avg > 25) status = "NORMAL";
    else status = "FREE_FLOW";
    return {
      name: r.name,
      forecast: avg,
      peak,
      status,
      nodes: r.nodes.map((n) => ({
        name: DISPLAY_NAMES[n.node_id] || n.node_id,
        forecast: n.forecast_1h,
        status: n.status,
        trend: n.trend,
      })),
    };
  });
});

async function load() {
  loading.value = true;
  try {
    const { data } = await api.get("/nav/status");
    navStatus.value = data;
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
        <p class="muted" style="margin:0;">Live traffic from AI pipeline (LightGBM + ConvLSTM)</p>
      </div>
      <Button icon="pi pi-refresh" label="Refresh" @click="load" :loading="loading" outlined />
    </div>

    <div class="road-list">
      <Card v-for="road in roads" :key="road.name">
        <template #content>
          <div style="display:flex; justify-content:space-between; align-items:center; gap:1rem;">
            <div style="flex:1;">
              <div style="font-weight:600; font-size:1.05rem;">{{ road.name }}</div>
              <div style="display:flex; align-items:center; gap:.5rem; margin-top:.4rem;">
                <ProgressBar
                  :value="road.forecast"
                  :showValue="false"
                  style="height:8px; flex:1; max-width:160px;"
                  :pt="{ value: { style: { background: forecastColor(road.forecast) } } }"
                />
                <span class="muted" style="font-size:.8rem;">{{ road.forecast.toFixed(1) }}% avg</span>
                <span class="muted" style="font-size:.75rem;">(peak {{ road.peak.toFixed(1) }}%)</span>
              </div>
              <div style="margin-top:.5rem; display:flex; flex-wrap:wrap; gap:.4rem;">
                <div v-for="node in road.nodes" :key="node.name" class="int-chip">
                  <span style="font-size:.75rem;">{{ node.name }}</span>
                  <span style="font-size:.65rem;" :style="{ color: node.trend === 'increasing' ? '#f97316' : node.trend === 'decreasing' ? '#22c55e' : '#94a3b8' }">
                    {{ node.trend === 'increasing' ? '↑' : node.trend === 'decreasing' ? '↓' : '→' }}
                  </span>
                  <Tag :severity="statusSeverity(node.status)" :value="node.forecast.toFixed(0) + '%'" style="font-size:.65rem;" />
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
.road-list { display: flex; flex-direction: column; gap: .75rem; }
.int-chip {
  display: flex; align-items: center; gap: .3rem;
  padding: .15rem .4rem; background: rgba(255,255,255,0.03);
  border-radius: 4px; border: 1px solid rgba(255,255,255,0.06);
}
</style>
