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

// Display names for intersections
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

const ROAD_DISPLAY = {
  "Neftchilar Ave": "Neftchilar Ave",
  "Babek Ave": "Babek Ave",
  "Tbilisi Ave": "Tbilisi Ave",
  "Z.Bunyadov Ave": "Z.Bunyadov Ave",
  "Nizami St": "M.Mushfig St",
  "H.Aliyev St": "A.Aliyev St",
  "Heydar Aliyev Ave": "H.Aliyev Ave",
};

function displayName(key) {
  return DISPLAY_NAMES[key] || key;
}

function displayRoad(road) {
  return ROAD_DISPLAY[road] || road;
}

// Real Baku coordinates for intersections
const COORDS = {
  "Neftchilar/Nizami": [40.3862, 49.8486],
  "Neftchilar/H.Aliyev": [40.3835, 49.8590],
  "Neftchilar/Heydar": [40.3808, 49.8700],
  "Babek/Nizami": [40.3955, 49.8465],
  "Babek/H.Aliyev": [40.3935, 49.8575],
  "Babek/Heydar": [40.3915, 49.8690],
  "Tbilisi/Nizami": [40.4060, 49.8450],
  "Tbilisi/H.Aliyev": [40.4040, 49.8560],
  "Bunyadov/Nizami": [40.4170, 49.8440],
  "Bunyadov/H.Aliyev": [40.4150, 49.8550],
  "Bunyadov/Heydar": [40.4130, 49.8680],
};

const EDGES = [
  ["Neftchilar/Nizami", "Neftchilar/H.Aliyev"],
  ["Neftchilar/H.Aliyev", "Neftchilar/Heydar"],
  ["Babek/Nizami", "Babek/H.Aliyev"],
  ["Babek/H.Aliyev", "Babek/Heydar"],
  ["Tbilisi/Nizami", "Tbilisi/H.Aliyev"],
  ["Bunyadov/Nizami", "Bunyadov/H.Aliyev"],
  ["Bunyadov/H.Aliyev", "Bunyadov/Heydar"],
  ["Neftchilar/Nizami", "Babek/Nizami"],
  ["Babek/Nizami", "Tbilisi/Nizami"],
  ["Tbilisi/Nizami", "Bunyadov/Nizami"],
  ["Neftchilar/H.Aliyev", "Babek/H.Aliyev"],
  ["Babek/H.Aliyev", "Tbilisi/H.Aliyev"],
  ["Tbilisi/H.Aliyev", "Bunyadov/H.Aliyev"],
  ["Neftchilar/Heydar", "Babek/Heydar"],
  ["Babek/Heydar", "Bunyadov/Heydar"],
];

const intersectionOptions = Object.keys(COORDS).map((key) => ({
  label: DISPLAY_NAMES[key] || key,
  value: key,
}));

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
  if (s === "CONGESTED") return "#ef4444";  // red
  if (s === "HEAVY") return "#f97316";       // orange
  if (s === "NORMAL") return "#4ade80";      // green (light traffic)
  return "#22c55e";                           // green (free flow)
}

function statusSeverity(s) {
  if (s === "CONGESTED") return "danger";
  if (s === "HEAVY") return "warn";
  if (s === "NORMAL") return "info";
  return "success";
}

function congestionToWeight(val) {
  return Math.max(4, Math.min(12, 4 + val * 20));
}

function initMap() {
  map = L.map("baku-map", {
    center: [40.3990, 49.8570],
    zoom: 13,
    zoomControl: true,
  });

  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    attribution: '&copy; OpenStreetMap &copy; CARTO',
    maxZoom: 19,
  }).addTo(map);

  markersLayer = L.layerGroup().addTo(map);
  edgesLayer = L.layerGroup().addTo(map);
  routeLayer = L.layerGroup().addTo(map);
}

function updateMapMarkers() {
  if (!map || !status.value) return;
  markersLayer.clearLayers();
  edgesLayer.clearLayers();

  const statusMap = {};
  for (const item of status.value.intersections) {
    statusMap[item.intersection] = item;
  }

  for (const [from, to] of EDGES) {
    const fromData = statusMap[from];
    const toData = statusMap[to];
    if (!fromData || !toData || !COORDS[from] || !COORDS[to]) continue;

    // Pick the worse status of the two endpoints
    const statusOrder = { FREE_FLOW: 0, NORMAL: 1, HEAVY: 2, CONGESTED: 3 };
    const fromRank = statusOrder[fromData.status] ?? 0;
    const toRank = statusOrder[toData.status] ?? 0;
    const lineStatus = fromRank >= toRank ? fromData.status : toData.status;
    const color = statusColor(lineStatus);

    L.polyline([COORDS[from], COORDS[to]], {
      color,
      weight: 5,
      opacity: 0.85,
    }).addTo(edgesLayer);
  }

  for (const item of status.value.intersections) {
    const coord = COORDS[item.intersection];
    if (!coord) continue;

    const color = statusColor(item.status);
    const marker = L.circleMarker(coord, {
      radius: 9,
      fillColor: color,
      color: "#fff",
      weight: 2,
      fillOpacity: 0.9,
    }).addTo(markersLayer);

    marker.bindPopup(`
      <div style="font-family:sans-serif; font-size:13px;">
        <b>${displayName(item.intersection)}</b><br/>
        Status: <span style="color:${color}; font-weight:bold;">${item.status.replace("_", " ")}</span><br/>
        Congestion: ${(item.congestion * 100).toFixed(1)}%
      </div>
    `);
  }
}

function drawRoute() {
  if (!map || !routeResult.value) return;
  routeLayer.clearLayers();

  const path = routeResult.value.smart.path;
  const coords = path.map((n) => COORDS[n]).filter(Boolean);

  if (coords.length > 1) {
    L.polyline(coords, {
      color: "#3b82f6",
      weight: 6,
      opacity: 0.9,
      dashArray: "10, 6",
    }).addTo(routeLayer);

    L.marker(coords[0], {
      icon: L.divIcon({
        className: "route-icon",
        html: '<div style="background:#22c55e; width:16px; height:16px; border-radius:50%; border:3px solid #fff;"></div>',
        iconSize: [16, 16],
        iconAnchor: [8, 8],
      }),
    }).addTo(routeLayer).bindPopup("Start: " + displayName(path[0]));

    L.marker(coords[coords.length - 1], {
      icon: L.divIcon({
        className: "route-icon",
        html: '<div style="background:#ef4444; width:16px; height:16px; border-radius:50%; border:3px solid #fff;"></div>',
        iconSize: [16, 16],
        iconAnchor: [8, 8],
      }),
    }).addTo(routeLayer).bindPopup("End: " + displayName(path[path.length - 1]));

    map.fitBounds(L.latLngBounds(coords).pad(0.2));
  }
}

async function loadStatus() {
  loadingStatus.value = true;
  try {
    const { data } = await api.get("/congestion/status");
    status.value = data;
    await nextTick();
    updateMapMarkers();
  } catch (e) {
    console.error(e);
  } finally {
    loadingStatus.value = false;
  }
}

async function loadForecast() {
  loadingForecast.value = true;
  try {
    const { data } = await api.get("/congestion/forecast");
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
    const { data } = await api.get("/congestion/route", {
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
  // Auto-refresh every 30 seconds
  refreshInterval = setInterval(loadStatus, 30000);
});

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval);
});
</script>

<template>
  <div class="nav-page">
    <!-- Map -->
    <div class="map-container">
      <div id="baku-map"></div>
      <div class="map-legend">
        <span><span class="dot" style="background:#22c55e;"></span> Free Flow</span>
        <span><span class="dot" style="background:#4ade80;"></span> Normal</span>
        <span><span class="dot" style="background:#f97316;"></span> Heavy</span>
        <span><span class="dot" style="background:#ef4444;"></span> Congested</span>
      </div>
    </div>

    <!-- Side panel -->
    <div class="side-panel">
      <h2 style="margin:0 0 .5rem 0; font-size:1.3rem;">Navigation</h2>
      <p class="muted" style="margin:0 0 1rem 0; font-size:.85rem;">AI-powered smart routing</p>

      <!-- Route planner -->
      <Card>
        <template #content>
          <div style="display:flex; flex-direction:column; gap:.75rem;">
            <div>
              <label class="muted" style="font-size:.8rem;">From</label>
              <Select v-model="startPoint" :options="intersectionOptions" optionLabel="label" optionValue="value" placeholder="Start point" fluid />
            </div>
            <div>
              <label class="muted" style="font-size:.8rem;">To</label>
              <Select v-model="endPoint" :options="intersectionOptions" optionLabel="label" optionValue="value" placeholder="Destination" fluid />
            </div>
            <Button
              label="Find Route"
              icon="pi pi-directions"
              :loading="loadingRoute"
              :disabled="!startPoint || !endPoint"
              @click="findRoute"
            />
          </div>

          <div v-if="routeResult" style="margin-top:1rem;">
            <div class="route-card smart">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="route-label">Smart Route</span>
                <span class="route-time-badge">{{ routeResult.smart.estimatedMinutes }} min</span>
              </div>
              <div class="route-roads">{{ routeResult.smart.roads.map(displayRoad).join(' → ') }}</div>
            </div>
            <div class="route-card default" style="margin-top:.5rem;">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="route-label" style="color:var(--muted);">Shortest</span>
                <span class="route-time-badge default-badge">{{ routeResult.default.estimatedMinutes }} min</span>
              </div>
              <div class="route-roads">{{ routeResult.default.roads.map(displayRoad).join(' → ') }}</div>
            </div>
            <div v-if="routeResult.savedMinutes > 0" class="saved-badge">
              Save ~{{ routeResult.savedMinutes }} min with smart routing!
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
          <div v-if="loadingStatus" style="text-align:center; padding:1rem;"><ProgressSpinner style="width:30px; height:30px;" /></div>
          <div v-else-if="status" class="status-list">
            <div v-for="item in status.intersections" :key="item.intersection" class="status-row">
              <span style="font-size:.8rem;">{{ displayName(item.intersection) }}</span>
              <div style="display:flex; align-items:center; gap:.3rem;">
                <span style="font-size:.7rem;" class="muted">{{ (item.congestion * 100).toFixed(0) }}%</span>
                <Tag :severity="statusSeverity(item.status)" :value="item.status.replace('_', ' ')" style="font-size:.7rem;" />
              </div>
            </div>
          </div>
        </template>
      </Card>

      <!-- Forecast -->
      <Card style="margin-top:.75rem;">
        <template #content>
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:.5rem;">
            <span style="font-weight:600; font-size:.95rem;">3h Forecast</span>
            <Button icon="pi pi-chart-line" text rounded size="small" @click="loadForecast" :loading="loadingForecast" />
          </div>
          <div v-if="!forecast" class="muted" style="font-size:.8rem;">Click to predict</div>
          <div v-else>
            <div v-for="h in forecast" :key="h.hour" class="forecast-item">
              <div style="display:flex; justify-content:space-between; margin-bottom:.4rem;">
                <span style="font-weight:600;">{{ h.hour }}</span>
                <span class="muted" style="font-size:.8rem;">Avg: {{ (h.avgCongestion * 100).toFixed(1) }}%</span>
              </div>
              <!-- Per-intersection predictions -->
              <div v-if="h.intersections" class="forecast-intersections">
                <div v-for="item in h.intersections.filter(i => i.status !== 'FREE_FLOW')" :key="item.intersection" class="forecast-int-row">
                  <span style="font-size:.75rem;">{{ displayName(item.intersection) }}</span>
                  <div style="display:flex; align-items:center; gap:.3rem;">
                    <span style="font-size:.7rem;" class="muted">{{ (item.congestion * 100).toFixed(0) }}%</span>
                    <Tag :severity="statusSeverity(item.status)" :value="item.status.replace('_',' ')" style="font-size:.6rem;" />
                  </div>
                </div>
                <div v-if="h.intersections.filter(i => i.status !== 'FREE_FLOW').length === 0" class="muted" style="font-size:.75rem;">
                  All roads clear
                </div>
              </div>
            </div>
          </div>
        </template>
      </Card>
    </div>
  </div>
</template>

<style scoped>
.nav-page {
  display: flex;
  height: calc(100vh - 60px);
  overflow: hidden;
}
.map-container {
  flex: 1;
  position: relative;
}
#baku-map {
  width: 100%;
  height: 100%;
}
.map-legend {
  position: absolute;
  bottom: 20px;
  left: 20px;
  background: rgba(15, 23, 42, 0.9);
  padding: 8px 14px;
  border-radius: 8px;
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #e2e8f0;
  z-index: 1000;
  backdrop-filter: blur(8px);
}
.dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 4px;
  vertical-align: middle;
}
.side-panel {
  width: 380px;
  padding: 1rem;
  overflow-y: auto;
  background: var(--bg);
  border-left: 1px solid var(--border);
}
@media (max-width: 768px) {
  .nav-page { flex-direction: column; }
  .map-container { height: 50vh; }
  .side-panel { width: 100%; height: 50vh; border-left: none; border-top: 1px solid var(--border); }
}
.route-card {
  padding: .6rem .75rem;
  border-radius: 8px;
  border: 1px solid var(--border);
}
.route-card.smart {
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.08);
}
.route-label { font-size: .8rem; font-weight: 600; }
.route-time-badge {
  background: #3b82f6;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: .75rem;
  font-weight: 700;
}
.route-time-badge.default-badge { background: #475569; }
.route-roads { font-size: .85rem; margin-top: .25rem; color: var(--muted); }
.saved-badge {
  margin-top: .5rem;
  padding: .4rem;
  background: rgba(34, 197, 94, 0.12);
  border: 1px solid #22c55e;
  border-radius: 6px;
  color: #22c55e;
  font-size: .8rem;
  text-align: center;
  font-weight: 600;
}
.status-list { display: flex; flex-direction: column; gap: .3rem; }
.status-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: .2rem 0;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.status-row:last-child { border-bottom: none; }
.forecast-item {
  padding: .4rem 0;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.forecast-item:last-child { border-bottom: none; }
.forecast-intersections {
  display: flex;
  flex-direction: column;
  gap: .2rem;
}
.forecast-int-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: .15rem .5rem;
  background: rgba(255,255,255,0.02);
  border-radius: 4px;
}
</style>
