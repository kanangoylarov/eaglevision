<script setup>
import { ref, onMounted } from "vue";
import api from "../api";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import Card from "primevue/card";
import Button from "primevue/button";
import Tag from "primevue/tag";

const trains = ref([]);
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
    const { data } = await api.get("/trains");
    trains.value = data;
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div class="container">
    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:1rem;">
      <h1 class="page-title" style="margin:0;">Trains</h1>
      <Button icon="pi pi-refresh" label="Refresh" @click="load" :loading="loading" outlined />
    </div>
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
          <Column field="trainCode" header="Code" sortable />
          <Column header="Station">
            <template #body="{ data }">{{ data.currentStation?.name }}</template>
          </Column>
          <Column field="humanCount" header="People" sortable />
          <Column header="Density">
            <template #body="{ data }">
              <Tag :severity="densitySeverity(data.aiResult)" :value="data.aiResult || '-'" />
            </template>
          </Column>
          <Column header="Updated">
            <template #body="{ data }">
              {{ new Date(data.updatedAt).toLocaleString() }}
            </template>
          </Column>
        </DataTable>
      </template>
    </Card>
  </div>
</template>
