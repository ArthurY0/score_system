<template>
  <v-chart :option="chartOption" autoresize style="height: 350px" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'

interface SubjectData {
  course_name: string
  score: number
  class_avg: number
}

const props = defineProps<{
  subjects: SubjectData[]
}>()

const chartOption = computed(() => {
  const maxVal = Math.max(
    ...props.subjects.map((s) => Math.max(s.score, s.class_avg)),
    100,
  )

  return {
    title: { text: '各科雷达图', left: 'center' },
    tooltip: {},
    legend: { bottom: 0, data: ['我的成绩', '班级均分'] },
    radar: {
      indicator: props.subjects.map((s) => ({
        name: s.course_name,
        max: Math.ceil(maxVal / 10) * 10,
      })),
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            name: '我的成绩',
            value: props.subjects.map((s) => s.score),
            areaStyle: { opacity: 0.2 },
            itemStyle: { color: '#409eff' },
          },
          {
            name: '班级均分',
            value: props.subjects.map((s) => s.class_avg),
            areaStyle: { opacity: 0.1 },
            lineStyle: { type: 'dashed' },
            itemStyle: { color: '#e6a23c' },
          },
        ],
      },
    ],
  }
})

defineExpose({ chartOption })
</script>
