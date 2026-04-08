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
const target = ref("train");
const targetOptions = [
  { label: "Train", value: "train" },
  { label: "Station", value: "station" },
];

const trainCode = ref("T-101");
const stationId = ref(null);
const stations = ref([]);

const file = ref(null);
const result = ref(null);
const loading = ref(false);
const fileUpload = useTemplateRef("fileUpload");

onMounted(async () => {
  try {
    const { data } = await api.get("/stations");
    stations.value = data;
  } catch {}
});

function onSelect(event) {
  file.value = event.files?.[0] || null;
}

function densitySeverity(ai) {
  if (!ai) return "secondary";
  if (ai.includes("high")) return "danger";
  if (ai.includes("medium")) return "warn";
  if (ai.includes("low")) return "success";
  return "info";
}

async function submit() {
  if (!file.value) {
    toast.add({ severity: "warn", summary: "No file", detail: "Choose a video or image first", life: 3000 });
    return;
  }
  if (target.value === "train" && !trainCode.value) {
    toast.add({ severity: "warn", summary: "Missing", detail: "Train code required", life: 3000 });
    return;
  }
  if (target.value === "station" && !stationId.value) {
    toast.add({ severity: "warn", summary: "Missing", detail: "Pick a station", life: 3000 });
    return;
  }

  loading.value = true;
  result.value = null;
  try {
    const form = new FormData();
    form.append("file", file.value);
    let url;
    if (target.value === "train") {
      form.append("trainCode", trainCode.value);
      url = "/trains/analyze";
    } else {
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

<template>
  <div class="container">
    <h1 class="page-title">Analyze</h1>
    <p class="muted" style="margin-top:-.5rem;">Upload footage to detect crowd density</p>

    <Card style="margin-top:1rem;">
      <template #content>
        <div style="display:flex; flex-direction:column; gap:1rem;">
          <SelectButton v-model="target" :options="targetOptions" optionLabel="label" optionValue="value" />

          <div v-if="target === 'train'">
            <label class="muted">Train code</label>
            <InputText v-model="trainCode" placeholder="T-101" fluid />
          </div>

          <div v-else>
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

    <Card v-if="result" style="margin-top:1rem;">
      <template #title>Result</template>
      <template #content>
        <div class="grid cols-2">
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
            <div>
              <Tag
                :severity="densitySeverity((result.train || result.station).aiResult)"
                :value="(result.train || result.station).aiResult"
                style="font-size:.95rem;"
              />
            </div>
          </div>
          <div v-if="result.prediction.framesAnalyzed" class="stat">
            <div class="label">Frames analyzed</div>
            <div class="value" style="font-size:1.2rem;">{{ result.prediction.framesAnalyzed }}</div>
          </div>
        </div>
      </template>
    </Card>
  </div>
</template>
