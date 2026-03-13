<template>
  <v-chart :option="chartOption" autoresize style="height: 350px" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'

const props = defineProps<{
  ultraLowRate: number
  lowRate: number
  passRate: number
  goodRate: number
  excellentRate: number
}>()

const chartOption = computed(() => ({
  title: { text: '成绩等级分布', left: 'center' },
  tooltip: { trigger: 'item', formatter: '{b}: {c}%' },
  legend: { bottom: 0 },
  series: [
    {
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: true,
      label: { show: true, formatter: '{b}\n{c}%' },
      data: [
        { name: '超低分', value: props.ultraLowRate, itemStyle: { color: '#f56c6c' } },
        { name: '低分', value: props.lowRate, itemStyle: { color: '#e6a23c' } },
        { name: '及格', value: props.passRate, itemStyle: { color: '#67c23a' } },
        { name: '良好', value: props.goodRate, itemStyle: { color: '#409eff' } },
        { name: '优秀', value: props.excellentRate, itemStyle: { color: '#6f7ad3' } },
      ],
    },
  ],
}))

defineExpose({ chartOption })
</script>
