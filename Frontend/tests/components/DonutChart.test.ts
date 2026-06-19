import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import DonutChart from '~/components/DonutChart.vue'

const DATA = [
  { label: 'Bitcoin', value: 60, color: '#f7931a' },
  { label: 'Ethereum', value: 30, color: '#627eea' },
  { label: 'Solana', value: 10, color: '#9945ff' },
]

describe('DonutChart', () => {
  it('renders an SVG element', () => {
    const wrapper = mount(DonutChart, { props: { data: DATA } })
    expect(wrapper.find('svg').exists()).toBe(true)
  })

  it('renders one circle arc per data entry', () => {
    const wrapper = mount(DonutChart, { props: { data: DATA } })
    expect(wrapper.findAll('circle').length).toBe(DATA.length)
  })

  it('applies the correct stroke color to each arc', () => {
    const wrapper = mount(DonutChart, { props: { data: DATA } })
    const circles = wrapper.findAll('circle')
    expect(circles[0].attributes('stroke')).toBe('#f7931a')
    expect(circles[1].attributes('stroke')).toBe('#627eea')
    expect(circles[2].attributes('stroke')).toBe('#9945ff')
  })

  it('emits hover event with label on mouseenter', async () => {
    const wrapper = mount(DonutChart, { props: { data: DATA } })
    await wrapper.findAll('circle')[0].trigger('mouseenter')
    expect(wrapper.emitted('hover')).toBeTruthy()
    expect(wrapper.emitted('hover')![0]).toEqual(['Bitcoin'])
  })

  it('emits hover event with null on mouseleave', async () => {
    const wrapper = mount(DonutChart, { props: { data: DATA } })
    await wrapper.findAll('circle')[0].trigger('mouseleave')
    expect(wrapper.emitted('hover')![0]).toEqual([null])
  })

  it('reduces opacity of non-active arcs when active is set', () => {
    const wrapper = mount(DonutChart, { props: { data: DATA, active: 'Bitcoin' } })
    const circles = wrapper.findAll('circle')
    // Active arc has opacity 1, others are dimmed
    expect(circles[0].attributes('style')).toContain('opacity: 1')
    expect(circles[1].attributes('style')).toContain('opacity: 0.4')
    expect(circles[2].attributes('style')).toContain('opacity: 0.4')
  })

  it('all arcs have full opacity when no active is set', () => {
    const wrapper = mount(DonutChart, { props: { data: DATA, active: null } })
    wrapper.findAll('circle').forEach((c) => {
      expect(c.attributes('style')).toContain('opacity: 1')
    })
  })

  it('renders no arcs for empty data', () => {
    const wrapper = mount(DonutChart, { props: { data: [] } })
    expect(wrapper.findAll('circle').length).toBe(0)
  })
})
