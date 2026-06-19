import { defineStore } from 'pinia'
import type { HoldingWithMarket } from '~/types/api'

interface Toast {
  id: number
  message: string
}

type HoldingModal = { mode: 'add' } | { mode: 'edit'; holding: HoldingWithMarket } | null

interface UiState {
  dark: boolean
  toasts: Toast[]
  query: string
  holdingModal: HoldingModal
  deleteHoldingId: number | null
}

const THEME_KEY = 'cc_theme'

export const useUiStore = defineStore('ui', {
  state: (): UiState => ({
    dark: true,
    toasts: [],
    query: '',
    holdingModal: null,
    deleteHoldingId: null,
  }),

  actions: {
    initTheme() {
      if (!import.meta.client) return
      // Dark navy is the default; only an explicit saved choice opts out of it.
      const saved = localStorage.getItem(THEME_KEY)
      this.dark = saved ? saved === 'dark' : true
      this.applyTheme()
    },
    applyTheme() {
      if (!import.meta.client) return
      document.documentElement.classList.toggle('dark', this.dark)
    },
    toggleTheme() {
      this.dark = !this.dark
      if (import.meta.client) localStorage.setItem(THEME_KEY, this.dark ? 'dark' : 'light')
      this.applyTheme()
    },

    setQuery(q: string) {
      this.query = q
    },

    toast(message: string) {
      const id = Date.now() + Math.random()
      this.toasts.push({ id, message })
      setTimeout(() => {
        this.toasts = this.toasts.filter((t) => t.id !== id)
      }, 2600)
    },

    // Holding modal + delete confirm (shared between dashboard, markets, coin page)
    openAddHolding() {
      this.holdingModal = { mode: 'add' }
    },
    openEditHolding(holding: HoldingWithMarket) {
      this.holdingModal = { mode: 'edit', holding }
    },
    closeHoldingModal() {
      this.holdingModal = null
    },
    askDeleteHolding(id: number) {
      this.deleteHoldingId = id
    },
    cancelDelete() {
      this.deleteHoldingId = null
    },
  },
})
