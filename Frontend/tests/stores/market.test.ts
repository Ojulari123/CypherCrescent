import { describe, it, expect, vi } from 'vitest'
import { useAuthStore } from '~/stores/auth'
import { useMarketStore } from '~/stores/market'

const RAW_COINS = [
  {
    id: 'bitcoin',
    symbol: 'btc',
    name: 'Bitcoin',
    image: 'https://example.com/btc.png',
    market_cap_rank: 1,
    current_price: 65000,
    market_cap: 1280000000000,
    price_change_percentage_1h_in_currency: 0.5,
    price_change_percentage_24h: 2.3,
    price_change_percentage_7d_in_currency: -1.2,
  },
  {
    id: 'ethereum',
    symbol: 'eth',
    name: 'Ethereum',
    image: null,
    market_cap_rank: 2,
    current_price: 3500,
    market_cap: 420000000000,
    price_change_percentage_1h_in_currency: null,
    price_change_percentage_24h: 1.1,
    price_change_percentage_7d_in_currency: 3.4,
  },
]

function setupAuth() {
  const auth = useAuthStore()
  auth.accessToken = 'test-token'
  return auth
}

describe('loadMarkets', () => {
  it('fetches coins and maps them', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockResolvedValue(RAW_COINS)

    const store = useMarketStore()
    await store.loadMarkets(['bitcoin', 'ethereum'])

    expect(store.coins).toHaveLength(2)
    expect(store.coins[0].id).toBe('bitcoin')
    expect(store.coins[0].symbol).toBe('BTC')  
    expect(store.coins[0].current_price).toBe(65000)
    expect(store.coins[1].price_change_percentage_1h).toBeNull()
    expect(store.loading).toBe(false)
  })

  it('sets error on failure', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockRejectedValue({ data: { detail: 'CoinGecko down' } })

    const store = useMarketStore()
    await store.loadMarkets(['bitcoin'])

    expect(store.error).toBe('CoinGecko down')
    expect(store.coins).toEqual([])
  })

  it('records fetch timestamps for all coins', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockResolvedValue(RAW_COINS)

    const store = useMarketStore()
    const before = Date.now()
    await store.loadMarkets()
    const after = Date.now()

    expect(store.coinFetchedAt['bitcoin']).toBeGreaterThanOrEqual(before)
    expect(store.coinFetchedAt['bitcoin']).toBeLessThanOrEqual(after)
  })
})

describe('loadTopMarkets', () => {
  it('loads page and sets topHasMore=true when full page returned', async () => {
    const auth = setupAuth()
    const fullPage = Array.from({ length: 50 }, (_, i) => ({ ...RAW_COINS[0], id: `coin-${i}`, symbol: 'x', name: `Coin ${i}` }))
    vi.spyOn(auth, 'authFetch').mockResolvedValue(fullPage)

    const store = useMarketStore()
    await store.loadTopMarkets(1)

    expect(store.topCoins).toHaveLength(50)
    expect(store.topHasMore).toBe(true)
    expect(store.topPage).toBe(1)
  })

  it('sets topHasMore=false on partial page', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockResolvedValue(RAW_COINS)  // only 2 items

    const store = useMarketStore()
    await store.loadTopMarkets(3)

    expect(store.topHasMore).toBe(false)
    expect(store.topPage).toBe(3)
  })

  it('passes page and per_page to the API', async () => {
    const auth = setupAuth()
    const spy = vi.spyOn(auth, 'authFetch').mockResolvedValue([])

    const store = useMarketStore()
    await store.loadTopMarkets(2)

    expect(spy).toHaveBeenCalledWith('/api/market/coins', expect.objectContaining({
      query: expect.objectContaining({ page: 2, per_page: 50 }),
    }))
  })
})

describe('ensureCoins', () => {
  it('skips coins already in cache that are fresh', async () => {
    const auth = setupAuth()
    const spy = vi.spyOn(auth, 'authFetch').mockResolvedValue([])

    const store = useMarketStore()
    store.coins = [{ id: 'bitcoin', symbol: 'BTC', name: 'Bitcoin', image: null, market_cap_rank: 1, current_price: 65000, market_cap: null, price_change_percentage_1h: null, price_change_percentage_24h: null, price_change_percentage_7d: null }]
    store.coinFetchedAt['bitcoin'] = Date.now()

    await store.ensureCoins(['bitcoin'])
    expect(spy).not.toHaveBeenCalled()
  })

  it('fetches stale coins', async () => {
    const auth = setupAuth()
    const spy = vi.spyOn(auth, 'authFetch').mockResolvedValue(RAW_COINS)

    const store = useMarketStore()
    store.coins = [{ id: 'bitcoin', symbol: 'BTC', name: 'Bitcoin', image: null, market_cap_rank: 1, current_price: 50000, market_cap: null, price_change_percentage_1h: null, price_change_percentage_24h: null, price_change_percentage_7d: null }]
    store.coinFetchedAt['bitcoin'] = Date.now() - 120_000  // 2 minutes ago → stale

    await store.ensureCoins(['bitcoin'])

    expect(spy).toHaveBeenCalled()
    expect(store.coins.find(c => c.id === 'bitcoin')?.current_price).toBe(65000)
  })

  it('fetches coins not yet in cache', async () => {
    const auth = setupAuth()
    const spy = vi.spyOn(auth, 'authFetch').mockResolvedValue([RAW_COINS[0]])

    const store = useMarketStore()
    await store.ensureCoins(['bitcoin'])

    expect(spy).toHaveBeenCalledWith('/api/market/coins', expect.objectContaining({
      query: expect.objectContaining({ ids: 'bitcoin' }),
    }))
    expect(store.coins).toHaveLength(1)
  })
})

describe('search', () => {
  it('clears results and skips fetch for empty query', async () => {
    const auth = setupAuth()
    const spy = vi.spyOn(auth, 'authFetch').mockResolvedValue([])

    const store = useMarketStore()
    store.searchResults = [{ id: 'bitcoin', symbol: 'BTC', name: 'Bitcoin', thumb: null, large: null, market_cap_rank: 1 }]
    await store.search('')

    expect(store.searchResults).toEqual([])
    expect(spy).not.toHaveBeenCalled()
  })

  it('fetches and sets results for a real query', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockResolvedValue([
      { id: 'bitcoin', symbol: 'BTC', name: 'Bitcoin', thumb: null, large: null, market_cap_rank: 1 },
    ])

    const store = useMarketStore()
    await store.search('bit')

    expect(store.searchResults).toHaveLength(1)
    expect(store.searchResults[0].id).toBe('bitcoin')
    expect(store.searching).toBe(false)
  })

  it('clears results on fetch error', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockRejectedValue(new Error('network'))

    const store = useMarketStore()
    await store.search('eth')

    expect(store.searchResults).toEqual([])
    expect(store.searching).toBe(false)
  })
})

describe('bySlug', () => {
  it('returns a coin by id', () => {
    const store = useMarketStore()
    store.coins = [{ id: 'bitcoin', symbol: 'BTC', name: 'Bitcoin', image: null, market_cap_rank: 1, current_price: 65000, market_cap: null, price_change_percentage_1h: null, price_change_percentage_24h: null, price_change_percentage_7d: null }]
    expect(store.bySlug('bitcoin')?.name).toBe('Bitcoin')
  })

  it('returns undefined for unknown slug', () => {
    const store = useMarketStore()
    expect(store.bySlug('notexist')).toBeUndefined()
  })
})
