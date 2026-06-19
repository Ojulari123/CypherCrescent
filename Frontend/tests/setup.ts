import { vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// Nuxt globals

vi.stubGlobal('$fetch', vi.fn())
vi.stubGlobal('useRuntimeConfig', () => ({ public: { apiBase: 'http://test.api' } }))

// Cross-store auto-imports (Nuxt re-exports stores as globals) 
// Import lazily so the active pinia is always the one set up per-test below.
import { useAuthStore } from '~/stores/auth'
import { useMarketStore } from '~/stores/market'
import { usePortfolioStore } from '~/stores/portfolio'
import { useWatchlistStore } from '~/stores/watchlist'
import { useUiStore } from '~/stores/ui'
import { useAlertStore } from '~/stores/alert'

vi.stubGlobal('useAuthStore', useAuthStore)
vi.stubGlobal('useMarketStore', useMarketStore)
vi.stubGlobal('usePortfolioStore', usePortfolioStore)
vi.stubGlobal('useWatchlistStore', useWatchlistStore)
vi.stubGlobal('useUiStore', useUiStore)
vi.stubGlobal('useAlertStore', useAlertStore)

// Per-test reset

beforeEach(() => {
  setActivePinia(createPinia())
  vi.resetAllMocks()   // clears queued mockResolvedValueOnce / mockRejectedValueOnce between tests
  localStorage.clear()
})
