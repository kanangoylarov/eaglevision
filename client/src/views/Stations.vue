<script setup>
import { ref, onMounted } from "vue";
import api from "../api";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import Card from "primevue/card";
import InputText from "primevue/inputtext";
import IconField from "primevue/iconfield";
import InputIcon from "primevue/inputicon";
import Tag from "primevue/tag";

const stations = ref([]);
const filter = ref("");
const loading = ref(true);

function densitySeverity(ai) {
  if (!ai) return "secondary";
  if (ai.includes("high")) return "danger";
  if (ai.includes("medium")) return "warn";
  if (ai.includes("low")) return "success";
  return "info";
}

onMounted(async () => {
  try {
    const { data } = await api.get("/stations");
    stations.value = data;
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="container">
    <h1 class="page-title">Stations</h1>
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
          <Column field="id" header="ID" style="width:80px;" />
          <Column field="name" header="Name" sortable />
          <Column field="humanCount" header="People" sortable />
          <Column header="Density">
            <template #body="{ data }">
              <Tag :severity="densitySeverity(data.aiResult)" :value="data.aiResult || '-'" />
            </template>
          </Column>
        </DataTable>
      </template>
    </Card>
  </div>
</template>
