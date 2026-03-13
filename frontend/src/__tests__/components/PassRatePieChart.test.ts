/**
 * TDD - Tests written FIRST.
 * User Journey: As a teacher, I want to see a pie chart showing the proportion
 * of ultra-low/low/pass/good/excellent students.
 */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import PassRatePieChart from '@/components/statistics/PassRatePieChart.vue'

vi.mock('vue-echarts', () => ({
  default: {
    name: 'VChart',
    props: ['option', 'autoresize'],
    template: '<div data-testid="echart" />',
  },
}))

describe('PassRatePieChart', () => {
  const defaultProps = {
    ultraLowRate: 10,
    lowRate: 15,
    passRate: 60,
    goodRate: 45,
    excellentRate: 20,
  }

  it('renders the chart', () => {
    const wrapper = mount(PassRatePieChart, { props: defaultProps })
    expect(wrapper.find('[data-testid="echart"]').exists()).toBe(true)
  })

  it('computes 5 segments in pie data', () => {
    const wrapper = mount(PassRatePieChart, { props: defaultProps })
    const vm = wrapper.vm as any
    const seriesData = vm.chartOption.series[0].data
    expect(seriesData).toHaveLength(5)
  })

  it('includes correct labels', () => {
    const wrapper = mount(PassRatePieChart, { props: defaultProps })
    const vm = wrapper.vm as any
    const names = vm.chartOption.series[0].data.map((d: any) => d.name)
    expect(names).toContain('超低分')
    expect(names).toContain('低分')
    expect(names).toContain('及格')
    expect(names).toContain('良好')
    expect(names).toContain('优秀')
  })
})
