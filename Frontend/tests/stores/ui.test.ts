import { describe, it, expect, vi } from 'vitest'
import { useUiStore } from '~/stores/ui'

const THEME_KEY = 'cc_theme'

const MOCK_HOLDING = {
  id: 1,
  coin_slug: 'bitcoin',
  quantity: 0.5,
  buy_price: 40000,
  name: 'Bitcoin',
  symbol: 'BTC',
  image: null,
  current_price: 65000,
  market_cap: null,
  price_change_percentage_24h: 2.3,
  value: 32500,
  cost_basis: 20000,
  pl: 12500,
  pl_percent: 62.5,
}

// Initial state
describe('initial state', () => {
  it('starts with dark mode on, empty toasts, no modal', () => {
    const store = useUiStore()
    expect(store.dark).toBe(true)
    expect(store.toasts).toEqual([])
    expect(store.holdingModal).toBeNull()
    expect(store.deleteHoldingId).toBeNull()
    expect(store.query).toBe('')
  })
})

// Theme
describe('toggleTheme', () => {
  it('flips dark mode and saves to localStorage', () => {
    const store = useUiStore()
    expect(store.dark).toBe(true)

    store.toggleTheme()
    expect(store.dark).toBe(false)
    expect(localStorage.getItem(THEME_KEY)).toBe('light')

    store.toggleTheme()
    expect(store.dark).toBe(true)
    expect(localStorage.getItem(THEME_KEY)).toBe('dark')
  })

  it('applies dark class to document root', () => {
    const store = useUiStore()
    store.dark = false
    store.toggleTheme()
    expect(document.documentElement.classList.contains('dark')).toBe(true)

    store.toggleTheme()
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })
})

describe('initTheme', () => {
  it('reads saved "light" and applies it', () => {
    localStorage.setItem(THEME_KEY, 'light')
    const store = useUiStore()
    store.initTheme()
    expect(store.dark).toBe(false)
  })

  it('defaults to dark when no saved preference', () => {
    const store = useUiStore()
    store.initTheme()
    expect(store.dark).toBe(true)
  })
})

describe('toast', () => {
  it('adds a toast with a message', () => {
    vi.useFakeTimers()
    const store = useUiStore()
    store.toast('Hello!')
    expect(store.toasts).toHaveLength(1)
    expect(store.toasts[0].message).toBe('Hello!')
    vi.useRealTimers()
  })

  it('removes the toast after 2600ms', () => {
    vi.useFakeTimers()
    const store = useUiStore()
    store.toast('Goodbye!')
    expect(store.toasts).toHaveLength(1)
    vi.advanceTimersByTime(2600)
    expect(store.toasts).toHaveLength(0)
    vi.useRealTimers()
  })

  it('can show multiple toasts simultaneously', () => {
    vi.useFakeTimers()
    const store = useUiStore()
    store.toast('First')
    store.toast('Second')
    expect(store.toasts).toHaveLength(2)
    vi.useRealTimers()
  })
})

describe('setQuery', () => {
  it('updates the search query', () => {
    const store = useUiStore()
    store.setQuery('bitcoin')
    expect(store.query).toBe('bitcoin')
  })
})

describe('holding modal', () => {
  it('openAddHolding sets mode to add', () => {
    const store = useUiStore()
    store.openAddHolding()
    expect(store.holdingModal).toEqual({ mode: 'add' })
  })

  it('openEditHolding sets mode to edit with holding', () => {
    const store = useUiStore()
    store.openEditHolding(MOCK_HOLDING)
    expect(store.holdingModal).toEqual({ mode: 'edit', holding: MOCK_HOLDING })
  })

  it('closeHoldingModal nulls the modal', () => {
    const store = useUiStore()
    store.openAddHolding()
    store.closeHoldingModal()
    expect(store.holdingModal).toBeNull()
  })
})

describe('delete confirm', () => {
  it('askDeleteHolding sets the id', () => {
    const store = useUiStore()
    store.askDeleteHolding(5)
    expect(store.deleteHoldingId).toBe(5)
  })

  it('cancelDelete clears the id', () => {
    const store = useUiStore()
    store.askDeleteHolding(5)
    store.cancelDelete()
    expect(store.deleteHoldingId).toBeNull()
  })
})
