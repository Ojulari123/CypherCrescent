import { describe, it, expect, vi } from 'vitest'
import { useAuthStore } from '~/stores/auth'
import { useMarketStore } from '~/stores/market'
import { useWatchlistStore } from '~/stores/watchlist'

const RAW_ITEM = {
  id: 42,
  coin_slug: 'bitcoin',
  created_at: '2026-01-01T00:00:00Z',
  name: 'Bitcoin',
  symbol: 'btc',
  image: 'https://example.com/btc.png',
  current_price: '65000.0',
  market_cap: '1280000000000',
  price_change_percentage_1h_in_currency: '0.5',
  price_change_percentage_24h: '2.3',
  price_change_percentage_7d_in_currency: '-1.2',
}

function setupAuth() {
  const auth = useAuthStore()
  auth.accessToken = 'test-token'
  return auth
}

// Getters
describe('getters', () => {
  it('slugs returns empty array when no items', () => {
    const store = useWatchlistStore()
    expect(store.slugs).toEqual([])
  })

  it('isWatched returns true for a watched slug', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockResolvedValue([RAW_ITEM])

    const store = useWatchlistStore()
    await store.load()

    expect(store.isWatched('bitcoin')).toBe(true)
    expect(store.isWatched('ethereum')).toBe(false)
  })

  it('itemFor returns the matching item', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockResolvedValue([RAW_ITEM])

    const store = useWatchlistStore()
    await store.load()

    expect(store.itemFor('bitcoin')?.id).toBe(42)
    expect(store.itemFor('ethereum')).toBeUndefined()
  })
})

// load
describe('load', () => {
  it('fetches and maps watchlist items', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockResolvedValue([RAW_ITEM])

    const store = useWatchlistStore()
    await store.load()

    expect(store.items).toHaveLength(1)
    expect(store.items[0].coin_slug).toBe('bitcoin')
    expect(store.items[0].symbol).toBe('BTC')  // uppercased
    expect(store.items[0].current_price).toBe(65000)
    expect(store.loading).toBe(false)
  })

  it('clears loading flag even on failure', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockRejectedValue(new Error('network'))

    const store = useWatchlistStore()
    await expect(store.load()).rejects.toThrow()
    expect(store.loading).toBe(false)
  })
})

// add
describe('add', () => {
  it('inserts optimistically and confirms with server id', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockResolvedValue({ id: 99, coin_slug: 'ethereum' })

    const store = useWatchlistStore()
    await store.add('ethereum')

    expect(store.items).toHaveLength(1)
    expect(store.items[0].id).toBe(99)  // server id
    expect(store.items[0].coin_slug).toBe('ethereum')
  })

  it('enriches new item from market store cache', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockResolvedValue({ id: 5, coin_slug: 'bitcoin' })

    const market = useMarketStore()
    market.coins = [{ id: 'bitcoin', symbol: 'BTC', name: 'Bitcoin', image: 'btc.png', market_cap_rank: 1, current_price: 65000, market_cap: null, price_change_percentage_1h: null, price_change_percentage_24h: 2.3, price_change_percentage_7d: null }]
    market.coinFetchedAt['bitcoin'] = Date.now()

    const store = useWatchlistStore()
    await store.add('bitcoin')

    expect(store.items[0].name).toBe('Bitcoin')
    expect(store.items[0].current_price).toBe(65000)
  })

  it('reverts optimistic insert when server returns error', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockRejectedValue(new Error('server error'))

    const store = useWatchlistStore()
    await expect(store.add('bitcoin')).rejects.toThrow()
    expect(store.items).toHaveLength(0)
  })

  it('is a no-op if coin is already watched', async () => {
    const auth = setupAuth()
    const spy = vi.spyOn(auth, 'authFetch')

    const store = useWatchlistStore()
    store.items = [{ id: 1, coin_slug: 'bitcoin', created_at: '', name: null, symbol: null, image: null, current_price: null, market_cap: null, price_change_percentage_1h: null, price_change_percentage_24h: null, price_change_percentage_7d: null }]

    await store.add('bitcoin')
    expect(spy).not.toHaveBeenCalled()
  })
})

// remove
describe('remove', () => {
  it('removes item optimistically and calls API', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockResolvedValue(undefined)

    const store = useWatchlistStore()
    store.items = [{ id: 42, coin_slug: 'bitcoin', created_at: '', name: null, symbol: null, image: null, current_price: null, market_cap: null, price_change_percentage_1h: null, price_change_percentage_24h: null, price_change_percentage_7d: null }]

    await store.remove(42)

    expect(store.items).toHaveLength(0)
    expect(auth.authFetch).toHaveBeenCalledWith('/api/watchlist/42', expect.objectContaining({ method: 'DELETE' }))
  })

  it('reverts removal when server returns error', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockRejectedValue(new Error('server error'))

    const store = useWatchlistStore()
    const item = { id: 42, coin_slug: 'bitcoin', created_at: '', name: null, symbol: null, image: null, current_price: null, market_cap: null, price_change_percentage_1h: null, price_change_percentage_24h: null, price_change_percentage_7d: null }
    store.items = [item]

    await expect(store.remove(42)).rejects.toThrow()
    expect(store.items).toHaveLength(1)
    expect(store.items[0].id).toBe(42)
  })

  it('is a no-op for unknown id', async () => {
    const auth = setupAuth()
    const spy = vi.spyOn(auth, 'authFetch')

    const store = useWatchlistStore()
    await store.remove(9999)

    expect(spy).not.toHaveBeenCalled()
  })
})

// toggle
describe('toggle', () => {
  it('calls add when coin is not watched', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockResolvedValue({ id: 1, coin_slug: 'bitcoin' })

    const store = useWatchlistStore()
    const addSpy = vi.spyOn(store, 'add')

    await store.toggle('bitcoin')

    expect(addSpy).toHaveBeenCalledWith('bitcoin')
  })

  it('calls remove when coin is already watched', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockResolvedValue(undefined)

    const store = useWatchlistStore()
    store.items = [{ id: 42, coin_slug: 'bitcoin', created_at: '', name: null, symbol: null, image: null, current_price: null, market_cap: null, price_change_percentage_1h: null, price_change_percentage_24h: null, price_change_percentage_7d: null }]
    const removeSpy = vi.spyOn(store, 'remove')

    await store.toggle('bitcoin')

    expect(removeSpy).toHaveBeenCalledWith(42)
  })
})
