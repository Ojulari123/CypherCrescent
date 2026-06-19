import { defineStore } from 'pinia'
import type { PriceAlert } from '~/types/api'
import { num } from '~/utils/format'

function mapAlert(raw: any): PriceAlert {
  return {
    id: raw.id,
    coin_slug: raw.coin_slug,
    target_price: num(raw.target_price),
    direction: raw.direction as 'above' | 'below',
    triggered: raw.triggered,
    triggered_at: raw.triggered_at ?? null,
    created_at: raw.created_at,
  }
}

interface AlertState {
  items: PriceAlert[]
  loading: boolean
  creating: boolean
}

export const useAlertStore = defineStore('alert', {
  state: (): AlertState => ({
    items: [],
    loading: false,
    creating: false,
  }),

  getters: {
    active: (s): PriceAlert[] => s.items.filter((a) => !a.triggered),
    triggered: (s): PriceAlert[] => s.items.filter((a) => a.triggered),
    activeCount: (s): number => s.items.filter((a) => !a.triggered).length,
    atLimit: (s): boolean => s.items.filter((a) => !a.triggered).length >= 10,
    hasActiveAlertFor: (s) => (slug: string): boolean =>
      s.items.some((a) => a.coin_slug === slug && !a.triggered),
    activeAlertsFor: (s) => (slug: string): PriceAlert[] =>
      s.items.filter((a) => a.coin_slug === slug && !a.triggered),
  },

  actions: {
    async load() {
      const auth = useAuthStore()
      this.loading = true
      try {
        const raw = await auth.authFetch<any[]>('/api/alerts')
        this.items = raw.map(mapAlert)
      } finally {
        this.loading = false
      }
    },

    async create(coin_slug: string, target_price: number, direction: 'above' | 'below') {
      const auth = useAuthStore()
      this.creating = true
      try {
        const raw = await auth.authFetch<any>('/api/alerts', {
          method: 'POST',
          body: { coin_slug, target_price, direction },
        })
        this.items.unshift(mapAlert(raw))
      } finally {
        this.creating = false
      }
    },

    async update(id: number, target_price: number, direction: 'above' | 'below') {
      const auth = useAuthStore()
      const raw = await auth.authFetch<any>(`/api/alerts/${id}`, {
        method: 'PATCH',
        body: { target_price, direction },
      })
      const idx = this.items.findIndex((a) => a.id === id)
      if (idx !== -1) this.items[idx] = mapAlert(raw)
    },

    async reactivate(id: number) {
      const auth = useAuthStore()
      const raw = await auth.authFetch<any>(`/api/alerts/${id}/reactivate`, { method: 'POST' })
      const idx = this.items.findIndex((a) => a.id === id)
      if (idx !== -1) this.items[idx] = mapAlert(raw)
    },

    async remove(id: number) {
      const auth = useAuthStore()
      await auth.authFetch(`/api/alerts/${id}`, { method: 'DELETE' })
      this.items = this.items.filter((a) => a.id !== id)
    },
  },
})
