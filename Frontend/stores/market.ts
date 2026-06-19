import { defineStore } from 'pinia'
import type { CoinMarket, ChartResponse, ChartRange, CoinSearchResult } from '~/types/api'
import { DEFAULT_MARKET_IDS } from '~/utils/coins'

function n(v: unknown): number | null {
  if (v === null || v === undefined || v === '') return null
  const x = typeof v === 'number' ? v : parseFloat(String(v))
  return Number.isFinite(x) ? x : null
}

function mapCoin(raw: any): CoinMarket {
  return {
    id: raw.id,
    symbol: (raw.symbol ?? '').toUpperCase(),
    name: raw.name,
    image: raw.image ?? null,
    market_cap_rank: raw.market_cap_rank ?? null,
    current_price: n(raw.current_price),
    market_cap: n(raw.market_cap),
    price_change_percentage_1h: n(raw.price_change_percentage_1h_in_currency),
    price_change_percentage_24h: n(raw.price_change_percentage_24h),
    price_change_percentage_7d: n(raw.price_change_percentage_7d_in_currency),
  }
}

const PER_PAGE = 50
// How long a cached coin's market data is considered fresh. ensureCoins re-fetches
// any coin older than this instead of trusting the cache forever.
const COIN_TTL_MS = 60_000

interface MarketState {
  coins: CoinMarket[]
  // Last time (ms epoch) each coin id's data was fetched, keyed by id.
  coinFetchedAt: Record<string, number>
  loading: boolean
  error: string | null
  searchResults: CoinSearchResult[]
  searching: boolean
  // Markets page: top coins by market cap, paginated independently of the cache above.
  topCoins: CoinMarket[]
  topPage: number
  topHasMore: boolean
  topLoading: boolean
}

export const useMarketStore = defineStore('market', {
  state: (): MarketState => ({
    coins: [],
    coinFetchedAt: {},
    loading: false,
    error: null,
    searchResults: [],
    searching: false,
    topCoins: [],
    topPage: 1,
    topHasMore: true,
    topLoading: false,
  }),

  getters: {
    bySlug: (s) => (slug: string) => s.coins.find((c) => c.id === slug),
  },

  actions: {
    async loadMarkets(ids: string[] = DEFAULT_MARKET_IDS) {
      const auth = useAuthStore()
      this.loading = true
      this.error = null
      try {
        const raw = await auth.authFetch<any[]>('/api/market/coins', { query: { ids: ids.join(',') } })
        this.coins = raw.map(mapCoin)
        const now = Date.now()
        for (const c of this.coins) this.coinFetchedAt[c.id] = now
      } catch (e: any) {
        this.error = e?.data?.detail || 'Failed to load market data'
      } finally {
        this.loading = false
      }
    },

    // Markets page: load a page of the top coins by market cap. CoinGecko has
    // thousands of coins, so this pages through them 50 at a time.
    async loadTopMarkets(page = 1) {
      const auth = useAuthStore()
      this.topLoading = true
      this.error = null
      try {
        const raw = await auth.authFetch<any[]>('/api/market/coins', { query: { page, per_page: PER_PAGE } })
        this.topCoins = raw.map(mapCoin)
        this.topPage = page
        this.topHasMore = raw.length === PER_PAGE
      } catch (e: any) {
        this.error = e?.data?.detail || 'Failed to load market data'
      } finally {
        this.topLoading = false
      }
    },

    // Ensure a set of coin ids are present AND fresh in the cache (used by
    // watchlist/holdings/coin detail). Fetches only ids that are missing or whose
    // cached data is older than COIN_TTL_MS, then refreshes those in place.
    async ensureCoins(ids: string[]) {
      const now = Date.now()
      const fresh = new Set(
        this.coins.filter((c) => now - (this.coinFetchedAt[c.id] ?? 0) < COIN_TTL_MS).map((c) => c.id),
      )
      const want = [...new Set(ids)].filter((id) => !fresh.has(id))
      if (want.length === 0) return
      const auth = useAuthStore()
      try {
        const raw = await auth.authFetch<any[]>('/api/market/coins', { query: { ids: want.join(',') } })
        const mapped = raw.map(mapCoin)
        const byId = new Map(this.coins.map((c) => [c.id, c]))
        for (const c of mapped) {
          byId.set(c.id, c) // replace stale entry (or add) with fresh data
          this.coinFetchedAt[c.id] = now
        }
        this.coins = [...byId.values()]
      } catch {
        // non-fatal
      }
    },

    async getChart(coinId: string, range: ChartRange): Promise<ChartResponse> {
      const auth = useAuthStore()
      return auth.authFetch<ChartResponse>(`/api/market/coins/${coinId}/chart`, { query: { range } })
    },

    async search(q: string) {
      if (!q.trim()) {
        this.searchResults = []
        return
      }
      const auth = useAuthStore()
      this.searching = true
      try {
        this.searchResults = await auth.authFetch<CoinSearchResult[]>('/api/market/search', { query: { q } })
      } catch {
        this.searchResults = []
      } finally {
        this.searching = false
      }
    },
  },
})
