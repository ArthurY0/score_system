<template>
  <v-chart :option="chartOption" autoresize style="height: 350px" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import type { ClassComparisonItem } from '@/api/statistics'

const props = defineProps<{
  data: ClassComparisonItem[]
}>()

const chartOption = computed(() => ({
  title: { text: '班级对比', left: 'center' },
  tooltip: { trigger: 'axis' },
  legend: { bottom: 0, data: ['平均分', '及格率', '优秀率'] },
  xAxis: {
    type: 'category',
    data: props.data.map((d) => d.class_name),
  },
  yAxis: { type: 'value' },
  series: [
    {
      name: '平均分',
      type: 'bar',
      data: props.data.map((d) => d.avg_score),
      itemStyle: { color: '#409eff' },
    },
    {
      name: '及格率',
      type: 'bar',
      data: props.data.map((d) => d.pass_rate),
      itemStyle: { color: '#67c23a' },
    },
    {
      name: '优秀率',
      type: 'bar',
      data: props.data.map((d) => d.excellent_rate),
      itemStyle: { color: '#6f7ad3' },
    },
  ],
}))

defineExpose({ chartOption })
</script>
