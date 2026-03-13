/**
 * TDD - Tests written FIRST.
 * User Journey: As a teacher, I want to see a bar chart of score distribution
 * so I can understand how students performed across different score ranges.
 */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ScoreDistributionChart from '@/components/statistics/ScoreDistributionChart.vue'

// Mock vue-echarts since it requires canvas
vi.mock('vue-echarts', () => ({
  default: {
    name: 'VChart',
    props: ['option', 'autoresize'],
    template: '<div data-testid="echart" />',
  },
}))

describe('ScoreDistributionChart', () => {
  const sampleData = [
    { range: '<30', count: 2 },
    { range: '30-39', count: 3 },
    { range: '40-59', count: 5 },
    { range: '60-69', count: 8 },
    { range: '70-84', count: 12 },
    { range: '85-100', count: 6 },
    { range: '100-150', count: 1 },
  ]

  it('renders the chart container', () => {
    const wrapper = mount(ScoreDistributionChart, {
      props: { data: sampleData },
    })
    expect(wrapper.find('[data-testid="echart"]').exists()).toBe(true)
  })

  it('computes chart option with correct categories', () => {
    const wrapper = mount(ScoreDistributionChart, {
      props: { data: sampleData },
    })
    const vm = wrapper.vm as any
    const opt = vm.chartOption
    expect(opt.xAxis.data).toEqual(['<30', '30-39', '40-59', '60-69', '70-84', '85-100', '100-150'])
  })

  it('computes chart option with correct values', () => {
    const wrapper = mount(ScoreDistributionChart, {
      props: { data: sampleData },
    })
    const vm = wrapper.vm as any
    const opt = vm.chartOption
    expect(opt.series[0].data).toEqual([2, 3, 5, 8, 12, 6, 1])
  })

  it('handles empty data', () => {
    const wrapper = mount(ScoreDistributionChart, {
      props: { data: [] },
    })
    const vm = wrapper.vm as any
    expect(vm.chartOption.xAxis.data).toEqual([])
  })
})
