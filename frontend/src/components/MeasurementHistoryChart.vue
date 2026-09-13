<script setup lang="ts">
import { MudaCard } from "@mudakit/ui";
import { Chart, type ChartData, type ChartOptions } from "chart.js/auto";
import { computed, onMounted, ref, useTemplateRef, watch } from "vue";

import type { Measurement } from "@/api";
import { formatDateTime } from "@/common/format";

const props = defineProps<{
  measurements: Measurement[];
}>();

const chartCanvas = useTemplateRef("chartCanvas");

const chart = ref<Chart | null>(null);
const chartOptions = computed(
  () =>
    ({
      animation: false,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          display: false,
        },
      },
      scales: {
        x: {
          ticks: {
            autoSkip: true,
            maxRotation: 0,
          },
        },
        y: {
          beginAtZero: false,
        },
      },
    }) satisfies ChartOptions,
);
const chartData = computed(() => {
  const data = [...props.measurements].reverse();
  return {
    labels: data.map((item) => formatDateTime(item.measured_at, "date")),
    datasets: [
      {
        data: data.map((item) => item.weight),
        fill: false,
      },
    ],
  } satisfies ChartData;
});

const initChart = () => {
  if (chartCanvas.value == null) {
    return null;
  }

  const ctx = chartCanvas.value.getContext("2d");
  if (ctx == null) {
    return null;
  }

  return new Chart(ctx, {
    type: "line",
    options: chartOptions.value,
    data: chartData.value,
  });
};

watch(
  [chartOptions, chartData],
  () => {
    if (chartCanvas.value == null) {
      return;
    }

    if (chart.value != null) {
      chart.value.destroy();
    }

    chart.value = initChart();
  },
  { deep: true },
);

onMounted(() => {
  chart.value = initChart();
});
</script>

<template>
  <MudaCard>
    <div class="absolute inset-4">
      <canvas ref="chartCanvas" />
    </div>
  </MudaCard>
</template>
