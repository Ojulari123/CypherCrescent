import { describe, it, expect, vi } from 'vitest'
import { useAuthStore } from '~/stores/auth'
import { usePortfolioStore } from '~/stores/portfolio'

const MOCK_DASHBOARD_RAW = {
  total_value: '1500.75',
  total_cost: '1200.00',
  total_pl: '300.75',
  total_pl_percent: '25.0625',
  top_performer: { coin_slug: 'bitcoin', name: 'Bitcoin', pl_percent: '42.5' },
  worst_performer: { coin_slug: 'ethereum', name: 'Ethereum', pl_percent: '-5.2' },
  holdings: [
    {
      id: 1,
      coin_slug: 'bitcoin',
      quantity: '0.5',
      buy_price: '40000.0',
      name: 'Bitcoin',
      symbol: 'btc',
      image: 'https://example.com/btc.png',
      current_price: '60000.0',
      market_cap: '1200000000000',
      price_change_percentage_24h: '2.5',
      value: '30000.0',
      cost_basis: '20000.0',
      pl: '10000.0',
      pl_percent: '50.0',
    },
  ],
  market_data_available: true,
}

function setupAuth() {
  const auth = useAuthStore()
  auth.accessToken = 'test-token'
  return auth
}

describe('getters', () => {
  it('holdings returns empty array when dashboard is null', () => {
    const store = usePortfolioStore()
    expect(store.holdings).toEqual([])
    expect(store.heldSlugs).toEqual([])
  })

  it('holdings returns dashboard.holdings when loaded', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockResolvedValue(MOCK_DASHBOARD_RAW)

    const store = usePortfolioStore()
    await store.loadDashboard()

    expect(store.holdings).toHaveLength(1)
    expect(store.heldSlugs).toEqual(['bitcoin'])
  })
})

describe('loadDashboard', () => {
  it('fetches and coerces numeric strings to numbers', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockResolvedValue(MOCK_DASHBOARD_RAW)

    const store = usePortfolioStore()
    await store.loadDashboard()

    expect(store.dashboard?.total_value).toBe(1500.75)
    expect(store.dashboard?.total_cost).toBe(1200)
    expect(store.dashboard?.total_pl).toBe(300.75)
    expect(store.dashboard?.holdings[0].current_price).toBe(60000)
    expect(store.dashboard?.holdings[0].symbol).toBe('BTC')
    expect(auth.authFetch).toHaveBeenCalledWith('/api/dashboard')
    expect(store.loading).toBe(false)
  })

  it('maps top and worst performer', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockResolvedValue(MOCK_DASHBOARD_RAW)

    const store = usePortfolioStore()
    await store.loadDashboard()

    expect(store.dashboard?.top_performer?.coin_slug).toBe('bitcoin')
    expect(store.dashboard?.top_performer?.pl_percent).toBe(42.5)
    expect(store.dashboard?.worst_performer?.pl_percent).toBe(-5.2)
  })

  it('sets error on failure', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockRejectedValue({ data: { detail: 'Server error' } })

    const store = usePortfolioStore()
    await store.loadDashboard()

    expect(store.error).toBe('Server error')
    expect(store.dashboard).toBeNull()
    expect(store.loading).toBe(false)
  })

  it('clears loading flag even on failure', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockRejectedValue(new Error('network'))

    const store = usePortfolioStore()
    await store.loadDashboard()

    expect(store.loading).toBe(false)
  })
})

describe('addHolding', () => {
  it('posts holding and reloads dashboard', async () => {
    const auth = setupAuth()
    const authFetchSpy = vi.spyOn(auth, 'authFetch')
      .mockResolvedValueOnce({ id: 10, coin_slug: 'bitcoin', quantity: 1, buy_price: 50000 }) // POST
      .mockResolvedValueOnce(MOCK_DASHBOARD_RAW)                                                // reload

    const store = usePortfolioStore()
    await store.addHolding({ coin_slug: 'bitcoin', quantity: 1, buy_price: 50000 })

    expect(authFetchSpy).toHaveBeenCalledWith('/api/holdings', expect.objectContaining({ method: 'POST' }))
    expect(store.dashboard).not.toBeNull()
    expect(store.mutating).toBe(false)
  })

  it('clears mutating flag even on failure', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockRejectedValue(new Error('fail'))

    const store = usePortfolioStore()
    await expect(store.addHolding({ coin_slug: 'bitcoin', quantity: 1, buy_price: 50000 })).rejects.toThrow()
    expect(store.mutating).toBe(false)
  })
})

describe('updateHolding', () => {
  it('patches holding and reloads dashboard', async () => {
    const auth = setupAuth()
    const authFetchSpy = vi.spyOn(auth, 'authFetch')
      .mockResolvedValueOnce({ id: 1, coin_slug: 'bitcoin', quantity: 2, buy_price: 45000 })
      .mockResolvedValueOnce(MOCK_DASHBOARD_RAW)

    const store = usePortfolioStore()
    await store.updateHolding(1, { quantity: 2 })

    expect(authFetchSpy).toHaveBeenCalledWith('/api/holdings/1', expect.objectContaining({ method: 'PATCH' }))
    expect(store.mutating).toBe(false)
  })
})

describe('deleteHolding', () => {
  it('deletes holding and reloads dashboard', async () => {
    const auth = setupAuth()
    const authFetchSpy = vi.spyOn(auth, 'authFetch')
      .mockResolvedValueOnce(undefined)
      .mockResolvedValueOnce(MOCK_DASHBOARD_RAW)

    const store = usePortfolioStore()
    await store.deleteHolding(1)

    expect(authFetchSpy).toHaveBeenCalledWith('/api/holdings/1', expect.objectContaining({ method: 'DELETE' }))
    expect(store.mutating).toBe(false)
  })
})
