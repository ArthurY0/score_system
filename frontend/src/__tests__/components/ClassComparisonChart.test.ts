/**
 * TDD - Tests written FIRST.
 * User Journey: As a teacher/admin, I want to see a grouped bar chart comparing
 * average scores and pass rates across classes in the same grade.
 */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ClassComparisonChart from '@/components/statistics/ClassComparisonChart.vue'

vi.mock('vue-echarts', () => ({
  default: {
    name: 'VChart',
    props: ['option', 'autoresize'],
    template: '<div data-testid="echart" />',
  },
}))

describe('ClassComparisonChart', () => {
  const sampleData = [
    { class_id: 1, class_name: '一班', avg_score: 75.2, pass_rate: 80, excellent_rate: 20, student_count: 40 },
    { class_id: 2, class_name: '二班', avg_score: 68.5, pass_rate: 65, excellent_rate: 12, student_count: 38 },
  ]

  it('renders the chart', () => {
    const wrapper = mount(ClassComparisonChart, { props: { data: sampleData } })
    expect(wrapper.find('[data-testid="echart"]').exists()).toBe(true)
  })

  it('uses class names as x-axis categories', () => {
    const wrapper = mount(ClassComparisonChart, { props: { data: sampleData } })
    const vm = wrapper.vm as any
    expect(vm.chartOption.xAxis.data).toEqual(['一班', '二班'])
  })

  it('has three series (avg, pass rate, excellent rate)', () => {
    const wrapper = mount(ClassComparisonChart, { props: { data: sampleData } })
    const vm = wrapper.vm as any
    expect(vm.chartOption.series).toHaveLength(3)
  })

  it('handles empty data', () => {
    const wrapper = mount(ClassComparisonChart, { props: { data: [] } })
    const vm = wrapper.vm as any
    expect(vm.chartOption.xAxis.data).toEqual([])
  })
})
