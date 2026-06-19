import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StatCard from '~/components/StatCard.vue'

describe('StatCard', () => {
  it('renders label and value', () => {
    const wrapper = mount(StatCard, { props: { label: 'Total Value', value: '$1,500.00' } })
    expect(wrapper.text()).toContain('Total Value')
    expect(wrapper.text()).toContain('$1,500.00')
  })

  it('renders icon slot content', () => {
    const wrapper = mount(StatCard, {
      props: { label: 'P/L', value: '+$300' },
      slots: { icon: '<svg data-testid="icon" />' },
    })
    expect(wrapper.find('[data-testid="icon"]').exists()).toBe(true)
  })

  it('renders sub slot when provided', () => {
    const wrapper = mount(StatCard, {
      props: { label: 'Holdings', value: '3 coins' },
      slots: { sub: '<span>+2.5%</span>' },
    })
    expect(wrapper.text()).toContain('+2.5%')
  })

  it('does not render sub section when no sub slot', () => {
    const wrapper = mount(StatCard, { props: { label: 'Holdings', value: '3' } })
    expect(wrapper.find('[class*="mt-1"]').exists()).toBe(false)
  })

  it('uses default accent color when not provided', () => {
    const wrapper = mount(StatCard, { props: { label: 'Test', value: '0' } })
    const iconCell = wrapper.find('span[style]')
    expect(iconCell.attributes('style')).toContain('#3861fb')
  })

  it('uses provided accent color', () => {
    const wrapper = mount(StatCard, { props: { label: 'Test', value: '0', accent: '#16a34a' } })
    const iconCell = wrapper.find('span[style]')
    expect(iconCell.attributes('style')).toContain('#16a34a')
  })
})
