<template>
  <v-chart :option="chartOption" autoresize style="height: 350px" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import type { TrendPoint } from '@/api/statistics'

const props = defineProps<{
  data: TrendPoint[]
}>()

const chartOption = computed(() => ({
  title: { text: '成绩趋势', left: 'center' },
  tooltip: { trigger: 'axis' },
  legend: { bottom: 0, data: ['个人成绩', '班级均分'] },
  xAxis: {
    type: 'category',
    data: props.data.map((d) => d.semester_name),
  },
  yAxis: { type: 'value', name: '分数' },
  series: [
    {
      name: '个人成绩',
      type: 'line',
      data: props.data.map((d) => d.student_score),
      smooth: true,
      itemStyle: { color: '#409eff' },
    },
    {
      name: '班级均分',
      type: 'line',
      data: props.data.map((d) => d.class_avg),
      smooth: true,
      lineStyle: { type: 'dashed' },
      itemStyle: { color: '#e6a23c' },
    },
  ],
}))

defineExpose({ chartOption })
</script>
