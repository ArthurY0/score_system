/**
 * TDD - Tests written FIRST.
 * User Journey: As a student/teacher, I want to see score trends across semesters
 * with both personal score and class average lines.
 */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ScoreTrendChart from '@/components/statistics/ScoreTrendChart.vue'

vi.mock('vue-echarts', () => ({
  default: {
    name: 'VChart',
    props: ['option', 'autoresize'],
    template: '<div data-testid="echart" />',
  },
}))

describe('ScoreTrendChart', () => {
  const sampleTrend = [
    { semester_id: 1, semester_name: '2024第一学期', student_score: 85, class_avg: 72 },
    { semester_id: 2, semester_name: '2024第二学期', student_score: 90, class_avg: 75 },
  ]

  it('renders the chart', () => {
    const wrapper = mount(ScoreTrendChart, { props: { data: sampleTrend } })
    expect(wrapper.find('[data-testid="echart"]').exists()).toBe(true)
  })

  it('has two series (personal + class avg)', () => {
    const wrapper = mount(ScoreTrendChart, { props: { data: sampleTrend } })
    const vm = wrapper.vm as any
    expect(vm.chartOption.series).toHaveLength(2)
  })

  it('uses semester names as x-axis', () => {
    const wrapper = mount(ScoreTrendChart, { props: { data: sampleTrend } })
    const vm = wrapper.vm as any
    expect(vm.chartOption.xAxis.data).toEqual(['2024第一学期', '2024第二学期'])
  })

  it('maps student scores to first series', () => {
    const wrapper = mount(ScoreTrendChart, { props: { data: sampleTrend } })
    const vm = wrapper.vm as any
    expect(vm.chartOption.series[0].data).toEqual([85, 90])
  })

  it('maps class avg to second series', () => {
    const wrapper = mount(ScoreTrendChart, { props: { data: sampleTrend } })
    const vm = wrapper.vm as any
    expect(vm.chartOption.series[1].data).toEqual([72, 75])
  })
})
