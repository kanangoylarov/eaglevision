<script setup>
import { ref, onMounted, onUnmounted, nextTick } from "vue";
import api from "../api";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import Card from "primevue/card";
import Button from "primevue/button";
import Select from "primevue/select";
import Tag from "primevue/tag";
import ProgressSpinner from "primevue/progressspinner";

const NODE_OPTIONS = [
  { label: "Sahil area", value: "neft_nizami" },
  { label: "Bayil road", value: "neft_aliyev" },
  { label: "Boulevard", value: "neft_heydar" },
  { label: "Memar Ajami", value: "babek_nizami" },
  { label: "Old City area", value: "babek_aliyev" },
  { label: "Hazi Aslanov rd.", value: "babek_heydar" },
  { label: "20 January area", value: "tbilisi_nizami" },
  { label: "Narimanov area", value: "tbilisi_aliyev" },
  { label: "Koroglu area", value: "bunyadov_nizami" },
  { label: "Gara Garayev area", value: "bunyadov_aliyev" },
  { label: "Hazi Aslanov m.", value: "bunyadov_heydar" },
];

const COORDS = {
  neft_nizami: [40.3862, 49.8486], neft_aliyev: [40.3835, 49.8590], neft_heydar: [40.3808, 49.8700],
  babek_nizami: [40.3955, 49.8465], babek_aliyev: [40.3935, 49.8575], babek_heydar: [40.3915, 49.8690],
  tbilisi_nizami: [40.4060, 49.8450], tbilisi_aliyev: [40.4040, 49.8560],
  bunyadov_nizami: [40.4170, 49.8440], bunyadov_aliyev: [40.4150, 49.8550], bunyadov_heydar: [40.4130, 49.8680],
  m_sahil: [40.3870, 49.8490], m_28may: [40.3940, 49.8535], m_ganjlik: [40.4020, 49.8550],
  m_narimanov: [40.4050, 49.8560], m_koroglu: [40.4160, 49.8550],
};

const EDGES = [
  ["neft_nizami", "neft_aliyev"], ["neft_aliyev", "neft_heydar"],
  ["babek_nizami", "babek_aliyev"], ["babek_aliyev", "babek_heydar"],
  ["tbilisi_nizami", "tbilisi_aliyev"],
  ["bunyadov_nizami", "bunyadov_aliyev"], ["bunyadov_aliyev", "bunyadov_heydar"],
  ["neft_nizami", "babek_nizami"], ["babek_nizami", "tbilisi_nizami"], ["tbilisi_nizami", "bunyadov_nizami"],
  ["neft_aliyev", "babek_aliyev"], ["babek_aliyev", "tbilisi_aliyev"], ["tbilisi_aliyev", "bunyadov_aliyev"],
  ["neft_heydar", "babek_heydar"], ["babek_heydar", "bunyadov_heydar"],
];

const METRO_EDGES = [
  ["m_sahil", "m_28may"], ["m_28may", "m_ganjlik"], ["m_ganjlik", "m_narimanov"], ["m_narimanov", "m_koroglu"],
];

const startPoint = ref(null);
const endPoint = ref(null);
const routeResult = ref(null);
const status = ref(null);
const forecast = ref(null);
const loadingStatus = ref(true);
const loadingRoute = ref(false);
const loadingForecast = ref(false);

let map = null;
let markersLayer = null;
let edgesLayer = null;
let routeLayer = null;

function statusColor(s) {
  if (s === "CONGESTED") return "#ef4444";
  if (s === "HEAVY") return "#f97316";
  if (s === "NORMAL") return "#4ade80";
  return "#22c55e";
}

function statusSeverity(s) {
  if (s === "CONGESTED") return "danger";
  if (s === "HEAVY") return "warn";
  if (s === "NORMAL") return "info";
  return "success";
}

function modeIcon(m) {
  if (m === "metro") return "pi pi-building";
  if (m === "walk") return "pi pi-user";
  return "pi pi-car";
}

function initMap() {
  map = L.map("baku-map", { center: [40.3990, 49.8570], zoom: 13 });
  L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
    attribution: '&copy; OpenStreetMap &copy; CARTO', maxZoom: 19,
  }).addTo(map);
  markersLayer = L.layerGroup().addTo(map);
  edgesLayer = L.layerGroup().addTo(map);
  routeLayer = L.layerGroup().addTo(map);
}

function updateMap() {
  if (!map || !status.value?.nodes) return;
  markersLayer.clearLayers();
  edgesLayer.clearLayers();

  const stateMap = {};
  for (const n of status.value.nodes) stateMap[n.node_id] = n;

  // Road edges
  for (const [from, to] of EDGES) {
    if (!COORDS[from] || !COORDS[to]) continue;
    const fs = stateMap[from], ts = stateMap[to];
    const worst = (fs && ts) ? ([fs, ts].sort((a, b) => b.forecast_1h - a.forecast_1h)[0]) : null;
    const color = worst ? statusColor(worst.status) : "#334155";
    L.polyline([COORDS[from], COORDS[to]], { color, weight: 5, opacity: 0.85 }).addTo(edgesLayer);
  }

  // Metro edges (dashed blue)
  for (const [from, to] of METRO_EDGES) {
    if (!COORDS[from] || !COORDS[to]) continue;
    L.polyline([COORDS[from], COORDS[to]], { color: "#60a5fa", weight: 3, opacity: 0.6, dashArray: "6,4" }).addTo(edgesLayer);
  }

  // Markers
  for (const n of status.value.nodes) {
    const coord = COORDS[n.node_id];
    if (!coord) continue;
    const isMetro = n.mode === "metro";
    const color = isMetro ? "#60a5fa" : statusColor(n.status);
    L.circleMarker(coord, {
      radius: isMetro ? 6 : 9, fillColor: color, color: "#fff", weight: 2, fillOpacity: 0.9,
    }).addTo(markersLayer).bindPopup(`
      <div style="font-family:sans-serif;font-size:13px;">
        <b>${n.name}</b> ${isMetro ? '(Metro)' : ''}<br/>
        Forecast: <b>${n.forecast_1h}%</b><br/>
        Status: <span style="color:${color};font-weight:bold;">${n.status.replace('_',' ')}</span><br/>
        Trend: ${n.trend}
      </div>
    `);
  }
}

function drawRoute() {
  if (!map || !routeResult.value?.routes?.length) return;
  routeLayer.clearLayers();

  const best = routeResult.value.routes[0];
  const coords = best.path.map((n) => COORDS[n]).filter(Boolean);

  if (coords.length > 1) {
    // Draw each edge segment with mode color
    for (const edge of best.edges) {
      const c1 = COORDS[edge.from], c2 = COORDS[edge.to];
      if (!c1 || !c2) continue;
      const color = edge.mode === "metro" ? "#60a5fa" : edge.mode === "walk" ? "#a78bfa" : "#3b82f6";
      const dash = edge.mode === "walk" ? "4,6" : edge.mode === "metro" ? "8,4" : null;
      L.polyline([c1, c2], { color, weight: 6, opacity: 0.9, dashArray: dash }).addTo(routeLayer);
    }

    // Start/end markers
    L.marker(coords[0], {
      icon: L.divIcon({ className: "", html: '<div style="background:#22c55e;width:16px;height:16px;border-radius:50%;border:3px solid #fff;"></div>', iconSize: [16, 16], iconAnchor: [8, 8] }),
    }).addTo(routeLayer);
    L.marker(coords[coords.length - 1], {
      icon: L.divIcon({ className: "", html: '<div style="background:#ef4444;width:16px;height:16px;border-radius:50%;border:3px solid #fff;"></div>', iconSize: [16, 16], iconAnchor: [8, 8] }),
    }).addTo(routeLayer);

    map.fitBounds(L.latLngBounds(coords).pad(0.2));
  }
}

async function loadStatus() {
  loadingStatus.value = true;
  try {
    const { data } = await api.get("/nav/status");
    status.value = data;
    await nextTick();
    updateMap();
  } catch (e) {
    console.error(e);
  } finally {
    loadingStatus.value = false;
  }
}

async function loadForecast() {
  loadingForecast.value = true;
  try {
    const { data } = await api.get("/nav/forecast");
    forecast.value = data;
  } catch (e) {
    console.error(e);
  } finally {
    loadingForecast.value = false;
  }
}

async function findRoute() {
  if (!startPoint.value || !endPoint.value) return;
  loadingRoute.value = true;
  routeResult.value = null;
  routeLayer?.clearLayers();
  try {
    const { data } = await api.get("/nav/route", {
      params: { start: startPoint.value, end: endPoint.value },
    });
    routeResult.value = data;
    await nextTick();
    drawRoute();
  } catch (e) {
    console.error(e);
  } finally {
    loadingRoute.value = false;
  }
}

let refreshInterval = null;
onMounted(async () => {
  await nextTick();
  initMap();
  await loadStatus();
  refreshInterval = setInterval(loadStatus, 30000);
});
onUnmounted(() => { if (refreshInterval) clearInterval(refreshInterval); });
</script>

<template>
  <div class="nav-page">
    <div class="map-container">
      <div id="baku-map"></div>
      <div class="map-legend" style="background: rgba(255, 255, 255, 0.9); border: 1px solid rgba(0, 0, 0, 0.1); color: var(--text);">
        <span><span class="dot" style="background:#22c55e;"></span> Free</span>
        <span><span class="dot" style="background:#4ade80;"></span> Normal</span>
        <span><span class="dot" style="background:#f97316;"></span> Heavy</span>
        <span><span class="dot" style="background:#ef4444;"></span> Congested</span>
        <span><span class="dot" style="background:var(--accent);"></span> Metro</span>
      </div>
    </div>

    <div class="side-panel">
      <h2 style="margin:0 0 .5rem 0; font-size:1.3rem; font-family:'Manrope', sans-serif; font-weight:700;">Navigation</h2>
      <p class="muted" style="margin:0 0 1rem 0; font-size:.85rem;">AI-powered multimodal routing</p>

      <!-- Route planner -->
      <Card>
        <template #content>
          <div style="display:flex; flex-direction:column; gap:.75rem;">
            <div>
              <label class="muted" style="font-size:.8rem;">From</label>
              <Select v-model="startPoint" :options="NODE_OPTIONS" optionLabel="label" optionValue="value" placeholder="Start point" fluid />
            </div>
            <div>
              <label class="muted" style="font-size:.8rem;">To</label>
              <Select v-model="endPoint" :options="NODE_OPTIONS" optionLabel="label" optionValue="value" placeholder="Destination" fluid />
            </div>
            <Button label="Find Route" icon="pi pi-directions" :loading="loadingRoute" :disabled="!startPoint || !endPoint" @click="findRoute" />
          </div>

          <!-- Route results -->
          <div v-if="routeResult?.routes" style="margin-top:1rem;">
            <div v-for="route in routeResult.routes" :key="route.rank" :class="['route-card', route.rank === 1 ? 'best' : '']" style="margin-bottom:.5rem;">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="display:flex; align-items:center; gap:.4rem;">
                  <i :class="route.type === 'multimodal' ? 'pi pi-building' : 'pi pi-car'" style="font-size:.85rem;"></i>
                  <span class="route-label">{{ route.label }}</span>
                  <Tag v-if="route.rank === 1" value="Best" severity="success" style="font-size:.6rem;" />
                </div>
                <span class="route-time-badge" :class="{ 'default-badge': route.rank !== 1 }" style="background:var(--accent); color:white; padding:0.25rem 0.75rem; border-radius:999px; font-size:.75rem; font-weight:600;">{{ route.totalTime }} min</span>
              </div>
              <div style="display:flex; gap:.75rem; margin-top:.3rem; font-size:.8rem;" class="muted">
                <span>{{ route.totalDistance }} km</span>
                <span>Risk: {{ route.risk }}/10</span>
                <span>{{ route.reliability }}% reliable</span>
              </div>
              <!-- Legs for multimodal -->
              <div v-if="route.legs" style="margin-top:.4rem;">
                <div v-for="(leg, i) in route.legs" :key="i" class="leg-row">
                  <i :class="modeIcon(leg.mode)" style="font-size:.75rem; width:16px;"></i>
                  <span style="font-size:.8rem;">{{ leg.mode === 'walk' ? 'Walk' : leg.mode === 'metro' ? 'Metro' : 'Drive' }}</span>
                  <span class="muted" style="font-size:.75rem;">{{ leg.time }} min</span>
                </div>
              </div>
              <!-- Road edges for drive -->
              <div v-else-if="route.roads?.length" style="margin-top:.3rem;">
                <span class="muted" style="font-size:.8rem;">{{ route.roads.join(' → ') }}</span>
              </div>
            </div>
          </div>
        </template>
      </Card>

      <!-- Live status -->
      <Card style="margin-top:.75rem;">
        <template #content>
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:.5rem;">
            <span style="font-weight:600; font-size:.95rem;">Live Traffic</span>
            <Button icon="pi pi-refresh" text rounded size="small" @click="loadStatus" :loading="loadingStatus" />
          </div>
          <div v-if="loadingStatus" style="text-align:center; padding:1rem;"><ProgressSpinner style="width:24px; height:24px;" strokeWidth="3" /></div>
          <div v-else-if="status?.nodes" class="status-list">
            <div v-for="n in status.nodes.filter(n => n.mode === 'road')" :key="n.node_id" class="status-row">
              <span style="font-size:.8rem;">{{ n.name }}</span>
              <div style="display:flex; align-items:center; gap:.3rem;">
                <span style="font-size:.7rem;" class="muted">{{ n.forecast_1h }}%</span>
                <Tag :severity="statusSeverity(n.status)" :value="n.status.replace('_',' ')" style="font-size:.7rem;" />
              </div>
            </div>
          </div>
        </template>
      </Card>

      <!-- LightGBM Forecast -->
      <Card style="margin-top:.75rem;">
        <template #content>
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:.5rem;">
            <span style="font-weight:600; font-size:.95rem;">AI Forecast (1h)</span>
            <Button icon="pi pi-chart-line" text rounded size="small" @click="loadForecast" :loading="loadingForecast" />
          </div>
          <div v-if="!forecast" class="muted" style="font-size:.8rem;">Click to predict</div>
          <div v-else class="status-list">
            <div v-for="f in forecast.forecasts" :key="f.node_id" class="status-row">
              <div>
                <span style="font-size:.8rem;">{{ f.name }}</span>
                <span v-if="f.mode === 'metro'" class="muted" style="font-size:.65rem; margin-left:.3rem;">metro</span>
              </div>
              <div style="display:flex; align-items:center; gap:.3rem;">
                <span style="font-size:.65rem;" :style="{ color: f.trend === 'increasing' ? '#f97316' : f.trend === 'decreasing' ? '#22c55e' : '#94a3b8' }">
                  {{ f.trend === 'increasing' ? '↑' : f.trend === 'decreasing' ? '↓' : '→' }}
                </span>
                <span style="font-size:.7rem;" class="muted">{{ f.forecast_1h }}%</span>
                <Tag :severity="statusSeverity(f.status)" :value="f.status.replace('_',' ')" style="font-size:.65rem;" />
              </div>
            </div>
          </div>
        </template>
      </Card>
    </div>
  </div>
</template>

<style scoped>
.nav-page { display: flex; height: calc(100vh - 60px); overflow: hidden; }
.map-container { flex: 1; position: relative; }
#baku-map { width: 100%; height: 100%; }
.map-legend {
  position: absolute; bottom: 20px; left: 20px; background: rgba(15,23,42,0.9);
  padding: 8px 14px; border-radius: 8px; display: flex; gap: 12px;
  font-size: 12px; color: #e2e8f0; z-index: 1000; backdrop-filter: blur(8px);
}
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 4px; vertical-align: middle; }
.side-panel { width: 380px; padding: 1rem; overflow-y: auto; background: var(--bg); border-left: 1px solid var(--border); }
@media (max-width: 768px) {
  .nav-page { flex-direction: column; }
  .map-container { height: 50vh; }
  .side-panel { width: 100%; height: 50vh; border-left: none; border-top: 1px solid var(--border); }
}
.route-card { padding: .6rem .75rem; border-radius: 8px; border: 1px solid var(--border); }
.route-card.best { border-color: #3b82f6; background: rgba(59,130,246,0.08); }
.route-label { font-size: .85rem; font-weight: 600; }
.route-time-badge { background: #3b82f6; color: white; padding: 2px 8px; border-radius: 12px; font-size: .75rem; font-weight: 700; }
.route-time-badge.default-badge { background: #475569; }
.leg-row { display: flex; align-items: center; gap: .4rem; padding: .15rem 0; }
.status-list { display: flex; flex-direction: column; gap: .3rem; }
.status-row { display: flex; justify-content: space-between; align-items: center; padding: .2rem 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
.status-row:last-child { border-bottom: none; }
</style>
