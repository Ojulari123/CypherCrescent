import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { useUiStore } from '~/stores/ui'
import { usePortfolioStore } from '~/stores/portfolio'
import ConfirmDialog from '~/components/ConfirmDialog.vue'

describe('ConfirmDialog', () => {
  it('is not visible when deleteHoldingId is null', () => {
    const ui = useUiStore()
    ui.deleteHoldingId = null
    const wrapper = mount(ConfirmDialog)
    expect(wrapper.find('[role="alertdialog"]').exists()).toBe(false)
  })

  it('is visible when deleteHoldingId is set', async () => {
    const ui = useUiStore()
    ui.deleteHoldingId = 42
    const wrapper = mount(ConfirmDialog)
    await wrapper.vm.$nextTick()
    expect(wrapper.find('[role="alertdialog"]').exists()).toBe(true)
  })

  it('shows the dialog heading and description', async () => {
    const ui = useUiStore()
    ui.deleteHoldingId = 1
    const wrapper = mount(ConfirmDialog)
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('Delete holding?')
  })

  it('calls ui.cancelDelete when Cancel is clicked', async () => {
    const ui = useUiStore()
    ui.deleteHoldingId = 1
    const wrapper = mount(ConfirmDialog)
    await wrapper.vm.$nextTick()
    const spy = vi.spyOn(ui, 'cancelDelete')
    await wrapper.findAll('button')[0].trigger('click')
    expect(spy).toHaveBeenCalledOnce()
  })

  it('calls portfolio.deleteHolding with the correct id on confirm', async () => {
    const ui = useUiStore()
    const portfolio = usePortfolioStore()
    ui.deleteHoldingId = 7
    vi.spyOn(portfolio, 'deleteHolding').mockResolvedValue(undefined as any)
    vi.spyOn(ui, 'cancelDelete')
    const wrapper = mount(ConfirmDialog)
    await wrapper.vm.$nextTick()
    const buttons = wrapper.findAll('button')
    const confirmBtn = buttons[buttons.length - 1]
    await confirmBtn.trigger('click')
    expect(portfolio.deleteHolding).toHaveBeenCalledWith(7)
  })

  it('shows "Deleting…" text while portfolio.mutating is true', async () => {
    const ui = useUiStore()
    const portfolio = usePortfolioStore()
    ui.deleteHoldingId = 1
    portfolio.mutating = true
    const wrapper = mount(ConfirmDialog)
    await wrapper.vm.$nextTick()
    const buttons = wrapper.findAll('button')
    const confirmBtn = buttons[buttons.length - 1]
    expect(confirmBtn.text()).toBe('Deleting…')
  })

  it('shows "Delete" text when not mutating', async () => {
    const ui = useUiStore()
    const portfolio = usePortfolioStore()
    ui.deleteHoldingId = 1
    portfolio.mutating = false
    const wrapper = mount(ConfirmDialog)
    await wrapper.vm.$nextTick()
    const buttons = wrapper.findAll('button')
    const confirmBtn = buttons[buttons.length - 1]
    expect(confirmBtn.text()).toBe('Delete')
  })
})
