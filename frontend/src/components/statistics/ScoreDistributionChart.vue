<template>
  <v-chart :option="chartOption" autoresize style="height: 350px" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import type { ScoreDistributionBucket } from '@/api/statistics'

const props = defineProps<{
  data: ScoreDistributionBucket[]
}>()

const chartOption = computed(() => ({
  title: { text: '分数段分布', left: 'center' },
  tooltip: { trigger: 'axis' },
  xAxis: {
    type: 'category',
    data: props.data.map((d) => d.range),
  },
  yAxis: { type: 'value', name: '人数' },
  series: [
    {
      type: 'bar',
      data: props.data.map((d) => d.count),
      itemStyle: {
        color: (params: any) => {
          const colors = ['#f56c6c', '#e6a23c', '#909399', '#67c23a', '#409eff', '#6f7ad3', '#b37feb']
          return colors[params.dataIndex % colors.length]
        },
      },
    },
  ],
}))

defineExpose({ chartOption })
</script>
