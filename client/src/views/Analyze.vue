<script setup>
import { ref, onMounted, useTemplateRef } from "vue";
import { useToast } from "primevue/usetoast";
import api from "../api";
import Card from "primevue/card";
import InputText from "primevue/inputtext";
import Button from "primevue/button";
import FileUpload from "primevue/fileupload";
import Tag from "primevue/tag";
import ProgressBar from "primevue/progressbar";
import SelectButton from "primevue/selectbutton";
import Select from "primevue/select";

const toast = useToast();

const target = ref("road");
const targetOptions = [
  { label: "Road", value: "road" },
  { label: "Train", value: "train" },
  { label: "Station", value: "station" },
];

const trainCode = ref("T-101");
const stationId = ref(null);
const roadId = ref(null);
const stations = ref([]);
const roads = ref([]);

const file = ref(null);
const result = ref(null);
const loading = ref(false);
const fileUpload = useTemplateRef("fileUpload");

onMounted(async () => {
  try {
    const [s, r] = await Promise.all([api.get("/stations"), api.get("/roads")]);
    stations.value = s.data;
    roads.value = r.data;
  } catch {}
});

function onSelect(event) {
  file.value = event.files?.[0] || null;
}

function statusSeverity(status) {
  if (!status) return "secondary";
  if (status === "CONGESTED") return "danger";
  if (status === "HEAVY") return "warn";
  if (status === "NORMAL") return "info";
  if (status === "FREE_FLOW") return "success";
  if (status.includes("high")) return "danger";
  if (status.includes("medium")) return "warn";
  return "success";
}

async function submit() {
  if (!file.value) {
    toast.add({ severity: "warn", summary: "No file", detail: "Choose a video or image first", life: 3000 });
    return;
  }

  loading.value = true;
  result.value = null;
  try {
    const form = new FormData();
    form.append("file", file.value);
    let url;

    if (target.value === "road") {
      if (!roadId.value) {
        toast.add({ severity: "warn", summary: "Missing", detail: "Pick a road", life: 3000 });
        loading.value = false;
        return;
      }
      form.append("roadId", roadId.value);
      url = "/roads/analyze";
    } else if (target.value === "train") {
      if (!trainCode.value) {
        toast.add({ severity: "warn", summary: "Missing", detail: "Train code required", life: 3000 });
        loading.value = false;
        return;
      }
      form.append("trainCode", trainCode.value);
      url = "/trains/analyze";
    } else {
      if (!stationId.value) {
        toast.add({ severity: "warn", summary: "Missing", detail: "Pick a station", life: 3000 });
        loading.value = false;
        return;
      }
      form.append("stationId", stationId.value);
      url = "/stations/analyze";
    }

    const { data } = await api.post(url, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    result.value = { target: target.value, ...data };
    toast.add({ severity: "success", summary: "Done", detail: "Analysis complete", life: 3000 });
    fileUpload.value?.clear();
    file.value = null;
  } catch (e) {
    toast.add({
      severity: "error",
      summary: "Failed",
      detail: e.response?.data?.error || "Analysis failed",
      life: 4000,
    });
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.analyze-hero {
  background: #ffffff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 10px 15px -3px rgba(0,0,0,0.08);
  border-radius: 16px;
  padding: 2rem;
  margin-bottom: 2rem;
}
</style>

<template>
  <div class="container">
    <div class="analyze-hero">
      <h1 class="page-title" style="margin:0;">Analyze</h1>
      <p class="muted" style="margin:.5rem 0 0 0; font-size:.95rem;">Upload footage for AI analysis</p>
    </div>

    <Card>
      <template #content>
        <div style="display:flex; flex-direction:column; gap:1rem;">
          <SelectButton v-model="target" :options="targetOptions" optionLabel="label" optionValue="value" />

          <!-- Road -->
          <div v-if="target === 'road'">
            <label class="muted">Road</label>
            <Select
              v-model="roadId"
              :options="roads"
              optionLabel="name"
              optionValue="id"
              placeholder="Select a road"
              filter
              fluid
            />
          </div>

          <!-- Train -->
          <div v-if="target === 'train'">
            <label class="muted">Train code</label>
            <InputText v-model="trainCode" placeholder="T-101" fluid />
          </div>

          <!-- Station -->
          <div v-if="target === 'station'">
            <label class="muted">Station</label>
            <Select
              v-model="stationId"
              :options="stations"
              optionLabel="name"
              optionValue="id"
              placeholder="Select a station"
              filter
              fluid
            />
          </div>

          <FileUpload
            ref="fileUpload"
            mode="basic"
            name="file"
            accept="video/*,image/*"
            :maxFileSize="200000000"
            chooseLabel="Choose file"
            chooseIcon="pi pi-upload"
            :auto="false"
            customUpload
            @select="onSelect"
          />

          <ProgressBar v-if="loading" mode="indeterminate" style="height:6px;" />

          <Button
            label="Upload & Analyze"
            icon="pi pi-bolt"
            :loading="loading"
            :disabled="!file"
            @click="submit"
          />
        </div>
      </template>
    </Card>

    <!-- Result -->
    <Card v-if="result" style="margin-top:1rem;">
      <template #title>Result</template>
      <template #content>
        <!-- Road result -->
        <div v-if="result.target === 'road'" class="grid cols-2">
          <div class="stat">
            <div class="label">Road</div>
            <div class="value" style="font-size:1.4rem;">{{ result.road.name }}</div>
          </div>
          <div class="stat">
            <div class="label">Route</div>
            <div style="font-size:1rem;">{{ result.road.fromPoint }} → {{ result.road.toPoint }}</div>
          </div>
          <div class="stat">
            <div class="label">Vehicles</div>
            <div class="value" style="color:#fb923c;">{{ result.road.vehicleCount }}</div>
          </div>
          <div class="stat">
            <div class="label">Coverage</div>
            <div class="value" style="font-size:1.2rem;">{{ result.road.coverage }}%</div>
          </div>
          <div class="stat">
            <div class="label">Status</div>
            <Tag :severity="statusSeverity(result.road.status)" :value="result.road.status.replace('_', ' ')" style="font-size:.95rem;" />
          </div>
        </div>

        <!-- Metro result -->
        <div v-else class="grid cols-2">
          <div class="stat" v-if="result.target === 'train'">
            <div class="label">Train</div>
            <div class="value" style="font-size:1.4rem;">{{ result.train.trainCode }}</div>
          </div>
          <div class="stat">
            <div class="label">Station</div>
            <div class="value" style="font-size:1.4rem;">
              {{ result.target === "train" ? result.train.currentStation?.name : result.station.name }}
            </div>
          </div>
          <div class="stat">
            <div class="label">People detected</div>
            <div class="value" style="color:#34d399;">
              {{ (result.train || result.station).humanCount }}
            </div>
          </div>
          <div class="stat">
            <div class="label">Density</div>
            <Tag
              :severity="statusSeverity((result.train || result.station).aiResult)"
              :value="(result.train || result.station).aiResult"
              style="font-size:.95rem;"
            />
          </div>
        </div>
      </template>
    </Card>
  </div>
</template>
