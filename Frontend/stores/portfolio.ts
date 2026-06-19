import { defineStore } from 'pinia'
import type { Dashboard, HoldingWithMarket, Holding } from '~/types/api'
import { num } from '~/utils/format'

function mapHolding(raw: any): HoldingWithMarket {
  return {
    id: raw.id,
    coin_slug: raw.coin_slug,
    quantity: num(raw.quantity),
    buy_price: num(raw.buy_price),
    name: raw.name ?? null,
    symbol: raw.symbol ? String(raw.symbol).toUpperCase() : null,
    image: raw.image ?? null,
    current_price: raw.current_price == null ? null : num(raw.current_price),
    market_cap: raw.market_cap == null ? null : num(raw.market_cap),
    price_change_percentage_24h: raw.price_change_percentage_24h == null ? null : num(raw.price_change_percentage_24h),
    value: raw.value == null ? null : num(raw.value),
    cost_basis: num(raw.cost_basis),
    pl: raw.pl == null ? null : num(raw.pl),
    pl_percent: raw.pl_percent == null ? null : num(raw.pl_percent),
  }
}

function mapDashboard(raw: any): Dashboard {
  return {
    total_value: num(raw.total_value),
    total_cost: num(raw.total_cost),
    total_pl: num(raw.total_pl),
    total_pl_percent: num(raw.total_pl_percent),
    top_performer: raw.top_performer
      ? { coin_slug: raw.top_performer.coin_slug, name: raw.top_performer.name, pl_percent: num(raw.top_performer.pl_percent) }
      : null,
    worst_performer: raw.worst_performer
      ? { coin_slug: raw.worst_performer.coin_slug, name: raw.worst_performer.name, pl_percent: num(raw.worst_performer.pl_percent) }
      : null,
    holdings: (raw.holdings ?? []).map(mapHolding),
    market_data_available: raw.market_data_available ?? true,
  }
}

interface PortfolioState {
  dashboard: Dashboard | null
  loading: boolean
  error: string | null
  mutating: boolean
  series: number[]
  seriesLoading: boolean
}

export const usePortfolioStore = defineStore('portfolio', {
  state: (): PortfolioState => ({
    dashboard: null,
    loading: false,
    error: null,
    mutating: false,
    series: [],
    seriesLoading: false,
  }),

  getters: {
    holdings: (s): HoldingWithMarket[] => s.dashboard?.holdings ?? [],
    heldSlugs: (s): string[] => (s.dashboard?.holdings ?? []).map((h) => h.coin_slug),
  },

  actions: {
    async loadDashboard() {
      const auth = useAuthStore()
      this.loading = true
      this.error = null
      try {
        const raw = await auth.authFetch<any>('/api/dashboard')
        this.dashboard = mapDashboard(raw)
      } catch (e: any) {
        this.error = e?.data?.detail || 'Failed to load dashboard'
      } finally {
        this.loading = false
      }
    },

    async addHolding(payload: { coin_slug: string; quantity: number; buy_price: number }) {
      const auth = useAuthStore()
      this.mutating = true
      try {
        await auth.authFetch<Holding>('/api/holdings', { method: 'POST', body: payload })
        await this.loadDashboard()
      } finally {
        this.mutating = false
      }
    },

    async updateHolding(id: number, payload: { quantity?: number; buy_price?: number }) {
      const auth = useAuthStore()
      this.mutating = true
      try {
        await auth.authFetch<Holding>(`/api/holdings/${id}`, { method: 'PATCH', body: payload })
        await this.loadDashboard()
      } finally {
        this.mutating = false
      }
    },

    // Build a real portfolio value series by summing each holding's historical price × quantity over the range.
    async loadPerformance(range: '24h' | '7d' | '30d') {
      const market = useMarketStore()
      const holds = this.holdings
      if (!holds.length) { this.series = []; return }
      this.seriesLoading = true
      try {
        const results = await Promise.all(
          holds.map(async (h) => {
            try {
              const c = await market.getChart(h.coin_slug, range)
              return { qty: h.quantity, prices: (c.points ?? []).map((p) => p.price) }
            } catch (e) {
              console.warn(`[portfolio] Failed to load chart for ${h.coin_slug}:`, e)
              return null
            }
          }),
        )
        const pairs = results.filter((r): r is { qty: number; prices: number[] } => !!r && r.prices.length > 1)
        if (!pairs.length) { this.series = []; return }
        const len = Math.min(...pairs.map((p) => p.prices.length))
        const series: number[] = []
        for (let i = 0; i < len; i++) {
          let sum = 0
          for (const p of pairs) sum += p.qty * p.prices[p.prices.length - len + i]
          series.push(sum)
        }
        this.series = series
      } finally {
        this.seriesLoading = false
      }
    },

    async deleteHolding(id: number) {
      const auth = useAuthStore()
      this.mutating = true
      try {
        await auth.authFetch(`/api/holdings/${id}`, { method: 'DELETE' })
        await this.loadDashboard()
      } finally {
        this.mutating = false
      }
    },
  },
})
