import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { useUiStore } from '~/stores/ui'
import { useMarketStore } from '~/stores/market'
import { usePortfolioStore } from '~/stores/portfolio'
import HoldingModal from '~/components/HoldingModal.vue'
import type { HoldingWithMarket } from '~/types/api'

const COIN = {
  id: 'bitcoin', symbol: 'BTC', name: 'Bitcoin', image: null,
  market_cap_rank: 1, current_price: 60000, market_cap: 1_300_000_000_000,
  price_change_percentage_1h: null, price_change_percentage_24h: 2.3, price_change_percentage_7d: null,
}

const HOLDING: HoldingWithMarket = {
  id: 1, coin_slug: 'bitcoin', quantity: 2.5, buy_price: 50000,
  name: 'Bitcoin', symbol: 'BTC', image: null,
  current_price: 60000, market_cap: null, price_change_percentage_24h: null,
  value: 150000, cost_basis: 125000, pl: 25000, pl_percent: 20,
}

function setup() {
  const ui = useUiStore()
  const market = useMarketStore()
  market.coins = [COIN]
  return { ui, market, portfolio: usePortfolioStore() }
}

// Mount first, then open via store so the watcher fires
async function mountAndOpen(mode: 'add' | 'edit') {
  const { ui } = setup()
  const wrapper = mount(HoldingModal)
  if (mode === 'add') ui.openAddHolding()
  else ui.openEditHolding(HOLDING)
  await wrapper.vm.$nextTick()
  return wrapper
}

// ── Visibility ────────────────────────────────────────────────────────────────

describe('visibility', () => {
  it('is hidden when holdingModal is null', () => {
    setup()
    const wrapper = mount(HoldingModal)
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false)
  })

  it('is visible when opened in add mode', async () => {
    const wrapper = await mountAndOpen('add')
    expect(wrapper.find('[role="dialog"]').exists()).toBe(true)
  })

  it('is visible when opened in edit mode', async () => {
    const wrapper = await mountAndOpen('edit')
    expect(wrapper.find('[role="dialog"]').exists()).toBe(true)
  })
})

// ── Title ─────────────────────────────────────────────────────────────────────

describe('title', () => {
  it('shows "Add holding" in add mode', async () => {
    const wrapper = await mountAndOpen('add')
    expect(wrapper.find('h3').text()).toBe('Add holding')
  })

  it('shows "Edit holding" in edit mode', async () => {
    const wrapper = await mountAndOpen('edit')
    expect(wrapper.find('h3').text()).toBe('Edit holding')
  })
})

// ── Edit mode pre-fill ────────────────────────────────────────────────────────

describe('edit mode pre-fill', () => {
  it('pre-fills quantity from the holding', async () => {
    const wrapper = await mountAndOpen('edit')
    const inputs = wrapper.findAll('input[type="number"]')
    expect(inputs[0].element.value).toBe('2.5')
  })

  it('pre-fills buy price from the holding', async () => {
    const wrapper = await mountAndOpen('edit')
    const inputs = wrapper.findAll('input[type="number"]')
    expect(inputs[1].element.value).toBe('50000')
  })

  it('disables the coin selector in edit mode', async () => {
    const wrapper = await mountAndOpen('edit')
    expect(wrapper.find('select').element.disabled).toBe(true)
  })

  it('does not disable the coin selector in add mode', async () => {
    const wrapper = await mountAndOpen('add')
    expect(wrapper.find('select').element.disabled).toBe(false)
  })
})

// ── Validation ────────────────────────────────────────────────────────────────

describe('validation', () => {
  it('shows quantity error after blur with no value', async () => {
    const wrapper = await mountAndOpen('add')
    await wrapper.findAll('input[type="number"]')[0].trigger('blur')
    expect(wrapper.text()).toContain('Quantity must be greater than 0')
  })

  it('shows buy price error after blur with no value', async () => {
    const wrapper = await mountAndOpen('add')
    // Fill quantity so qErr is empty; the single error line then shows bErr
    await wrapper.findAll('input[type="number"]')[0].setValue('1')
    await wrapper.findAll('input[type="number"]')[1].trigger('blur')
    expect(wrapper.text()).toContain('Buy price must be greater than 0')
  })

  it('submit button is disabled when form is invalid', async () => {
    const wrapper = await mountAndOpen('add')
    // qty and buy are empty → parseFloat('') = NaN → valid = false
    const submitBtn = wrapper.findAll('button').find(b => b.text().includes('Add holding') || b.text().includes('Saving'))
    expect(submitBtn!.element.disabled).toBe(true)
  })

  it('submit button is enabled when qty and buy are valid', async () => {
    const wrapper = await mountAndOpen('add')
    const inputs = wrapper.findAll('input[type="number"]')
    await inputs[0].setValue('1')
    await inputs[1].setValue('50000')
    const submitBtn = wrapper.findAll('button').find(b => b.text().includes('Add holding'))
    expect(submitBtn!.element.disabled).toBe(false)
  })
})

// ── P&L preview ───────────────────────────────────────────────────────────────

describe('P&L preview', () => {
  it('shows cost basis as qty × buy price', async () => {
    const wrapper = await mountAndOpen('add')
    const inputs = wrapper.findAll('input[type="number"]')
    await inputs[0].setValue('2')
    await inputs[1].setValue('50000')
    // cost = 2 × 50000 = $100,000
    expect(wrapper.text()).toContain('$100,000')
  })

  it('shows current value as qty × current price', async () => {
    const wrapper = await mountAndOpen('add')
    await wrapper.findAll('input[type="number"]')[0].setValue('2')
    await wrapper.findAll('input[type="number"]')[1].setValue('50000')
    // marketValue = 2 × 60000 = $120,000
    expect(wrapper.text()).toContain('$120,000')
  })
})

// ── Submit ────────────────────────────────────────────────────────────────────

describe('submit', () => {
  it('calls portfolio.addHolding with correct args in add mode', async () => {
    const { portfolio } = setup()
    vi.spyOn(portfolio, 'addHolding').mockResolvedValue(undefined as any)
    const wrapper = await mountAndOpen('add')
    await wrapper.findAll('input[type="number"]')[0].setValue('1.5')
    await wrapper.findAll('input[type="number"]')[1].setValue('45000')
    await wrapper.findAll('button').find(b => b.text().includes('Add holding'))!.trigger('click')
    expect(portfolio.addHolding).toHaveBeenCalledWith({ coin_slug: 'bitcoin', quantity: 1.5, buy_price: 45000 })
  })

  it('calls portfolio.updateHolding with correct args in edit mode', async () => {
    const { portfolio } = setup()
    vi.spyOn(portfolio, 'updateHolding').mockResolvedValue(undefined as any)
    const wrapper = await mountAndOpen('edit')
    const inputs = wrapper.findAll('input[type="number"]')
    await inputs[0].setValue('3')
    await inputs[1].setValue('55000')
    await wrapper.findAll('button').find(b => b.text().includes('Save changes'))!.trigger('click')
    expect(portfolio.updateHolding).toHaveBeenCalledWith(1, { quantity: 3, buy_price: 55000 })
  })

  it('calls ui.closeHoldingModal on success', async () => {
    const { ui, portfolio } = setup()
    vi.spyOn(portfolio, 'addHolding').mockResolvedValue(undefined as any)
    const spy = vi.spyOn(ui, 'closeHoldingModal')
    const wrapper = await mountAndOpen('add')
    await wrapper.findAll('input[type="number"]')[0].setValue('1')
    await wrapper.findAll('input[type="number"]')[1].setValue('50000')
    await wrapper.findAll('button').find(b => b.text().includes('Add holding'))!.trigger('click')
    await wrapper.vm.$nextTick()
    expect(spy).toHaveBeenCalled()
  })

  it('shows API error message on failure', async () => {
    const { portfolio } = setup()
    vi.spyOn(portfolio, 'addHolding').mockRejectedValue({ data: { detail: 'Coin already in portfolio' } })
    const wrapper = await mountAndOpen('add')
    await wrapper.findAll('input[type="number"]')[0].setValue('1')
    await wrapper.findAll('input[type="number"]')[1].setValue('50000')
    await wrapper.findAll('button').find(b => b.text().includes('Add holding'))!.trigger('click')
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('Coin already in portfolio')
  })

  it('shows "Saving…" text while portfolio.mutating', async () => {
    const { portfolio } = setup()
    portfolio.mutating = true
    const wrapper = await mountAndOpen('add')
    expect(wrapper.findAll('button').find(b => b.text().includes('Saving'))!.exists()).toBe(true)
  })
})
