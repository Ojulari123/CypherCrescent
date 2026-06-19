import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { useUiStore } from '~/stores/ui'
import AppToasts from '~/components/AppToasts.vue'

describe('AppToasts', () => {
  it('renders no toasts when the store is empty', () => {
    const ui = useUiStore()
    ui.toasts = []
    const wrapper = mount(AppToasts)
    expect(wrapper.findAll('[class*="rounded-lg"]').length).toBe(0)
  })

  it('renders one element per toast', async () => {
    const ui = useUiStore()
    ui.toasts = [
      { id: 1, message: 'Added to watchlist' },
      { id: 2, message: 'Alert set' },
    ]
    const wrapper = mount(AppToasts)
    await wrapper.vm.$nextTick()
    expect(wrapper.findAll('[class*="rounded-lg"]').length).toBe(2)
  })

  it('displays the toast message text', async () => {
    const ui = useUiStore()
    ui.toasts = [{ id: 1, message: 'Holding removed' }]
    const wrapper = mount(AppToasts)
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('Holding removed')
  })

  it('displays multiple different messages', async () => {
    const ui = useUiStore()
    ui.toasts = [
      { id: 1, message: 'Alert deleted' },
      { id: 2, message: 'Added to watchlist' },
    ]
    const wrapper = mount(AppToasts)
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('Alert deleted')
    expect(wrapper.text()).toContain('Added to watchlist')
  })
})
