import { vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '~/stores/auth'
import { useMarketStore } from '~/stores/market'
import { usePortfolioStore } from '~/stores/portfolio'
import { useWatchlistStore } from '~/stores/watchlist'
import { useUiStore } from '~/stores/ui'
import { useAlertStore } from '~/stores/alert'

vi.stubGlobal('$fetch', vi.fn())
vi.stubGlobal('useRuntimeConfig', () => ({ public: { apiBase: 'http://test.api' } }))
vi.stubGlobal('useAuthStore', useAuthStore)
vi.stubGlobal('useMarketStore', useMarketStore)
vi.stubGlobal('usePortfolioStore', usePortfolioStore)
vi.stubGlobal('useWatchlistStore', useWatchlistStore)
vi.stubGlobal('useUiStore', useUiStore)
vi.stubGlobal('useAlertStore', useAlertStore)

beforeEach(() => {
  setActivePinia(createPinia())
  vi.resetAllMocks()
  localStorage.clear()
})
