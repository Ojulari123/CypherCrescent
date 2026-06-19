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

    // Optimistic add: show the row immediately (enriched from the market cache
    // when available), then confirm with the server. Revert on failure.
    async add(coin_slug: string) {
      if (this.isWatched(coin_slug)) return
      const auth = useAuthStore()
      const c = useMarketStore().bySlug(coin_slug)
      const tempId = -Date.now()
      this.items.unshift({
        id: tempId,
        coin_slug,
        created_at: new Date().toISOString(),
        name: c?.name ?? null,
        symbol: c?.symbol ?? null,
        image: c?.image ?? null,
        current_price: c?.current_price ?? null,
        market_cap: c?.market_cap ?? null,
        price_change_percentage_1h: c?.price_change_percentage_1h ?? null,
        price_change_percentage_24h: c?.price_change_percentage_24h ?? null,
        price_change_percentage_7d: c?.price_change_percentage_7d ?? null,
      })
      try {
        const res = await auth.authFetch<any>('/api/watchlist', { method: 'POST', body: { coin_slug } })
        const added = this.items.find((i) => i.id === tempId)
        if (added && res?.id != null) added.id = res.id // swap temp id for the real one
      } catch (e) {
        this.items = this.items.filter((i) => i.id !== tempId) // revert
        throw e
      }
    },

    // Optimistic remove: drop the row immediately, re-insert it if the server rejects.
    async remove(itemId: number) {
      const auth = useAuthStore()
      const idx = this.items.findIndex((i) => i.id === itemId)
      if (idx === -1) return
      const [removed] = this.items.splice(idx, 1)
      try {
        await auth.authFetch(`/api/watchlist/${itemId}`, { method: 'DELETE' })
      } catch (e) {
        this.items.splice(idx, 0, removed) // revert
        throw e
      }
    },

    // Toggle by coin slug (adds, or removes the matching item).
    async toggle(coin_slug: string) {
      const existing = this.itemFor(coin_slug)
      if (existing) await this.remove(existing.id)
      else await this.add(coin_slug)
    },
  },
})
