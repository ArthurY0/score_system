/**
 * TDD - Tests written FIRST.
 * User Journey: As a teacher, I want to see key score metrics at a glance
 * (average, max, min, pass rate, etc.) so I can quickly assess class performance.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StatCard from '@/components/statistics/StatCard.vue'

describe('StatCard', () => {
  const defaultProps = {
    title: '平均分',
    value: 72.5,
    suffix: '分',
  }

  it('renders title and value', () => {
    const wrapper = mount(StatCard, { props: defaultProps })
    expect(wrapper.text()).toContain('平均分')
    expect(wrapper.text()).toContain('72.5')
  })

  it('renders suffix when provided', () => {
    const wrapper = mount(StatCard, { props: defaultProps })
    expect(wrapper.text()).toContain('分')
  })

  it('renders percentage suffix for rate values', () => {
    const wrapper = mount(StatCard, { props: { title: '及格率', value: 85.0, suffix: '%' } })
    expect(wrapper.text()).toContain('85')
    expect(wrapper.text()).toContain('%')
  })

  it('renders with zero value', () => {
    const wrapper = mount(StatCard, { props: { title: '最低分', value: 0, suffix: '分' } })
    expect(wrapper.text()).toContain('0')
  })

  it('applies color prop when provided', () => {
    const wrapper = mount(StatCard, {
      props: { ...defaultProps, color: '#67c23a' },
    })
    const valueEl = wrapper.find('[data-testid="stat-value"]')
    expect(valueEl.attributes('style')).toContain('color:')
  })
})
