/**
 * TDD - Tests written FIRST.
 * User Journey: As a student, I want to see a radar chart showing how my scores
 * compare to the class average across all subjects.
 */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import StudentRadarChart from '@/components/statistics/StudentRadarChart.vue'

vi.mock('vue-echarts', () => ({
  default: {
    name: 'VChart',
    props: ['option', 'autoresize'],
    template: '<div data-testid="echart" />',
  },
}))

describe('StudentRadarChart', () => {
  const sampleSubjects = [
    { course_name: '数学', score: 92, class_avg: 75 },
    { course_name: '语文', score: 85, class_avg: 78 },
    { course_name: '英语', score: 70, class_avg: 72 },
  ]

  it('renders the chart', () => {
    const wrapper = mount(StudentRadarChart, { props: { subjects: sampleSubjects } })
    expect(wrapper.find('[data-testid="echart"]').exists()).toBe(true)
  })

  it('creates radar indicator from subject names', () => {
    const wrapper = mount(StudentRadarChart, { props: { subjects: sampleSubjects } })
    const vm = wrapper.vm as any
    const indicators = vm.chartOption.radar.indicator
    expect(indicators.map((i: any) => i.name)).toEqual(['数学', '语文', '英语'])
  })

  it('has two series data entries (student + class avg)', () => {
    const wrapper = mount(StudentRadarChart, { props: { subjects: sampleSubjects } })
    const vm = wrapper.vm as any
    const data = vm.chartOption.series[0].data
    expect(data).toHaveLength(2)
    expect(data[0].value).toEqual([92, 85, 70])
    expect(data[1].value).toEqual([75, 78, 72])
  })

  it('handles single subject', () => {
    const wrapper = mount(StudentRadarChart, {
      props: { subjects: [{ course_name: '数学', score: 90, class_avg: 80 }] },
    })
    const vm = wrapper.vm as any
    expect(vm.chartOption.radar.indicator).toHaveLength(1)
  })
})
