<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import api from "../api";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import Card from "primevue/card";
import Tag from "primevue/tag";
import Button from "primevue/button";
import InputText from "primevue/inputtext";
import IconField from "primevue/iconfield";
import InputIcon from "primevue/inputicon";
import TabView from "primevue/tabview";
import TabPanel from "primevue/tabpanel";

const stations = ref([]);
const trains = ref([]);
const filter = ref("");
const loading = ref(true);

function densitySeverity(ai) {
  if (!ai) return "secondary";
  if (ai.includes("high")) return "danger";
  if (ai.includes("medium")) return "warn";
  if (ai.includes("low")) return "success";
  return "info";
}

async function load() {
  loading.value = true;
  try {
    const [s, t] = await Promise.all([api.get("/stations"), api.get("/trains")]);
    stations.value = s.data;
    trains.value = t.data;
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
        <h1 class="page-title" style="margin:0;">Metro</h1>
        <p class="muted" style="margin:0;">Stations & trains crowd density</p>
      </div>
      <Button icon="pi pi-refresh" label="Refresh" @click="load" :loading="loading" outlined />
    </div>

    <TabView>
      <TabPanel header="Stations">
        <Card>
          <template #content>
            <div style="display:flex; justify-content:flex-end; margin-bottom:1rem;">
              <IconField>
                <InputIcon class="pi pi-search" />
                <InputText v-model="filter" placeholder="Search stations..." />
              </IconField>
            </div>
            <DataTable
              :value="stations"
              :loading="loading"
              :globalFilterFields="['name']"
              :globalFilter="filter"
              stripedRows
              paginator
              :rows="10"
              responsiveLayout="stack"
              breakpoint="640px"
            >
              <Column field="name" header="Station" sortable />
              <Column field="humanCount" header="People" sortable style="width:120px;" />
              <Column header="Density" style="width:200px;">
                <template #body="{ data }">
                  <Tag :severity="densitySeverity(data.aiResult)" :value="data.aiResult || 'No data'" />
                </template>
              </Column>
            </DataTable>
          </template>
        </Card>
      </TabPanel>

      <TabPanel header="Trains">
        <Card>
          <template #content>
            <DataTable
              :value="trains"
              :loading="loading"
              stripedRows
              paginator
              :rows="10"
              responsiveLayout="stack"
              breakpoint="640px"
            >
              <Column field="trainCode" header="Code" sortable style="width:120px;" />
              <Column header="Station">
                <template #body="{ data }">{{ data.currentStation?.name }}</template>
              </Column>
              <Column field="humanCount" header="People" sortable style="width:120px;" />
              <Column header="Density" style="width:200px;">
                <template #body="{ data }">
                  <Tag :severity="densitySeverity(data.aiResult)" :value="data.aiResult || '-'" />
                </template>
              </Column>
            </DataTable>
          </template>
        </Card>
      </TabPanel>
    </TabView>
  </div>
</template>
