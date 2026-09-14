<script setup lang="ts">
import { Chart, type ChartData, type ChartOptions } from "chart.js/auto";
import { computed, onMounted, ref, useTemplateRef, watch } from "vue";

import type { Measurement } from "@/api";
import { DEFAULT_USER_COLOR } from "@/common/color";
import { formatDateTime } from "@/common/format";

const props = defineProps<{
  measurements: Measurement[];
}>();

const chartCanvas = useTemplateRef("chartCanvas");

const chart = ref<Chart | null>(null);
const chartMeasurements = computed(() => [...props.measurements].reverse());
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
          display: true,
          labels: {
            usePointStyle: true,
            boxWidth: 8,
          },
        },
        tooltip: {
          callbacks: {
            afterLabel: (context) => {
              const measurement = chartMeasurements.value[context.dataIndex];
              return measurement == null ? "" : `User: ${measurement.user?.name ?? "Unassigned"}`;
            },
          },
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
  const users = new Map<number | null, { name: string; color: string }>();
  for (const measurement of chartMeasurements.value) {
    const id = measurement.user?.id ?? null;
    users.set(id, {
      name: measurement.user?.name ?? "Unassigned",
      color: measurement.user?.color ?? DEFAULT_USER_COLOR,
    });
  }

  return {
    labels: chartMeasurements.value.map((item) => formatDateTime(item.measured_at, "date")),
    datasets: [...users.entries()].map(([userId, user]) => ({
      label: user.name,
      data: chartMeasurements.value.map((item) => ((item.user?.id ?? null) === userId ? item.weight : null)),
      borderColor: user.color,
      backgroundColor: user.color,
      pointBackgroundColor: user.color,
      pointRadius: 4,
      pointHoverRadius: 6,
      tension: 0.25,
      spanGaps: true,
      fill: false,
    })),
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
  <div class="absolute inset-4">
    <canvas ref="chartCanvas" />
  </div>
</template>
