import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AreaChart from '~/components/AreaChart.vue'

const VALUES = [100, 120, 90, 150, 130]

describe('AreaChart', () => {
  it('renders an SVG element', () => {
    const wrapper = mount(AreaChart, { props: { values: VALUES, color: '#3861fb' } })
    expect(wrapper.find('svg').exists()).toBe(true)
  })

  it('renders a filled area path and a line path when values are provided', () => {
    const wrapper = mount(AreaChart, { props: { values: VALUES, color: '#3861fb' } })
    const paths = wrapper.findAll('path')
    expect(paths.length).toBeGreaterThanOrEqual(2)
    paths.forEach((p) => expect(p.attributes('d')).toBeTruthy())
  })

  it('renders empty paths when values array is empty', () => {
    const wrapper = mount(AreaChart, { props: { values: [], color: '#3861fb' } })
    const paths = wrapper.findAll('path')
    paths.forEach((p) => expect(p.attributes('d') ?? '').toBe(''))
  })

  it('shows min and max price labels', () => {
    const wrapper = mount(AreaChart, { props: { values: VALUES, color: '#3861fb' } })
    const text = wrapper.text()
    expect(text).toContain('$90')
    expect(text).toContain('$150')
  })

  it('uses the provided color for the line stroke', () => {
    const wrapper = mount(AreaChart, { props: { values: VALUES, color: '#ff0000' } })
    const linePath = wrapper.findAll('path').find((p) => p.attributes('stroke') === '#ff0000')
    expect(linePath).toBeDefined()
  })

  it('respects the height prop on the SVG', () => {
    const wrapper = mount(AreaChart, { props: { values: VALUES, color: '#3861fb', height: 400 } })
    expect(wrapper.find('svg').attributes('height')).toBe('400')
  })

  it('does not show hover tooltip by default', () => {
    const wrapper = mount(AreaChart, { props: { values: VALUES, color: '#3861fb' } })
    const tooltip = wrapper.find('.pointer-events-none.absolute')
    expect(tooltip.exists()).toBe(false)
  })
})
