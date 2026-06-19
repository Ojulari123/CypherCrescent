import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ChangeBadge from '~/components/ChangeBadge.vue'

describe('ChangeBadge', () => {
  it('renders "—" when value is null', () => {
    const wrapper = mount(ChangeBadge, { props: { value: null } })
    expect(wrapper.text()).toBe('—')
    expect(wrapper.find('span[style*="fontSize"]').exists()).toBe(false)
  })

  it('shows ▲ arrow for positive values', () => {
    const wrapper = mount(ChangeBadge, { props: { value: 3.45 } })
    expect(wrapper.text()).toContain('▲')
    expect(wrapper.text()).toContain('3.45%')
  })

  it('shows ▼ arrow for negative values', () => {
    const wrapper = mount(ChangeBadge, { props: { value: -2.1 } })
    expect(wrapper.text()).toContain('▼')
    expect(wrapper.text()).toContain('2.10%')
  })

  it('shows absolute value (no minus sign) for negative', () => {
    const wrapper = mount(ChangeBadge, { props: { value: -5.678 } })
    expect(wrapper.text()).not.toContain('-')
    expect(wrapper.text()).toContain('5.68%')
  })

  it('shows no arrow for zero (neutral by default)', () => {
    const wrapper = mount(ChangeBadge, { props: { value: 0 } })
    expect(wrapper.text()).not.toContain('▲')
    expect(wrapper.text()).not.toContain('▼')
    expect(wrapper.text()).toContain('0.00%')
  })

  it('shows arrow for zero when showZeroNeutral is false', () => {
    const wrapper = mount(ChangeBadge, { props: { value: 0, showZeroNeutral: false } })
    expect(wrapper.text()).toContain('▲')
  })
})
