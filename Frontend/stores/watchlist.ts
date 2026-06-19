import { defineStore } from 'pinia'
import type { WatchlistItem } from '~/types/api'
import { num } from '~/utils/format'

function mapItem(raw: any): WatchlistItem {
  return {
    id: raw.id,
    coin_slug: raw.coin_slug,
    created_at: raw.created_at,
    name: raw.name ?? null,
    symbol: raw.symbol ? String(raw.symbol).toUpperCase() : null,
    image: raw.image ?? null,
    current_price: raw.current_price == null ? null : num(raw.current_price),
    market_cap: raw.market_cap == null ? null : num(raw.market_cap),
    price_change_percentage_1h: raw.price_change_percentage_1h_in_currency == null ? null : num(raw.price_change_percentage_1h_in_currency),
    price_change_percentage_24h: raw.price_change_percentage_24h == null ? null : num(raw.price_change_percentage_24h),
    price_change_percentage_7d: raw.price_change_percentage_7d_in_currency == null ? null : num(raw.price_change_percentage_7d_in_currency),
  }
}

interface WatchlistState {
  items: WatchlistItem[]
  loading: boolean
}

export const useWatchlistStore = defineStore('watchlist', {
  state: (): WatchlistState => ({ items: [], loading: false }),

  getters: {
    slugs: (s): string[] => s.items.map((i) => i.coin_slug),
    isWatched: (s) => (slug: string): boolean => s.items.some((i) => i.coin_slug === slug),
    itemFor: (s) => (slug: string): WatchlistItem | undefined => s.items.find((i) => i.coin_slug === slug),
  },

  actions: {
    async load() {
      const auth = useAuthStore()
      this.loading = true
      try {
        const raw = await auth.authFetch<any[]>('/api/watchlist')
        this.items = raw.map(mapItem)
      } finally {
        this.loading = false
      }
    },

    async add(coin_slug: string) {
      const auth = useAuthStore()
      await auth.authFetch('/api/watchlist', { method: 'POST', body: { coin_slug } })
      await this.load()
    },

    async remove(itemId: number) {
      const auth = useAuthStore()
      await auth.authFetch(`/api/watchlist/${itemId}`, { method: 'DELETE' })
      this.items = this.items.filter((i) => i.id !== itemId)
    },

    // Toggle by coin slug (adds, or removes the matching item).
    async toggle(coin_slug: string) {
      const existing = this.itemFor(coin_slug)
      if (existing) await this.remove(existing.id)
      else await this.add(coin_slug)
    },
  },
})
