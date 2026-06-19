<script setup lang="ts">
import { Loader2, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { watchDebounced } from '@vueuse/core'

const market = useMarketStore()
const ui = useUiStore()

onMounted(() => {
  if (!market.topCoins.length) market.loadTopMarkets(1)
})

// When searching, discover coins beyond the current page via /market/search,
// then hydrate their market data so they appear in the table.
watchDebounced(
  () => ui.query,
  async (q) => {
    if (!q.trim()) return
    await market.search(q)
    const ids = market.searchResults.slice(0, 12).map((r) => r.id)
    if (ids.length) await market.ensureCoins(ids)
  },
  { debounce: 350 },
)

const searching = computed(() => !!ui.query.trim())

const rows = computed(() => {
  const q = ui.query.toLowerCase().trim()
  if (!q) return market.topCoins
  return market.coins.filter((c) => `${c.name}${c.symbol}${c.id}`.toLowerCase().includes(q))
})

function goToPage(page: number) {
  if (page < 1) return
  market.loadTopMarkets(page)
  if (import.meta.client) window.scrollTo({ top: 0, behavior: 'smooth' })
}
</script>

<template>
  <div class="space-y-4">
    <div>
      <h1 class="text-xl font-bold md:text-2xl">Cryptocurrency Prices by Market Cap</h1>
      <p class="text-sm text-muted-foreground">Live market data via CoinGecko. Star to watch, click a column header to sort, click a row for the full page.</p>
    </div>

    <CoinTableSkeleton v-if="market.topLoading && !market.topCoins.length" />
    <div v-else-if="market.error && !market.topCoins.length" class="rounded-xl border border-red-500/30 bg-red-500/5 p-5 text-sm text-red-500">
      {{ market.error }} <button class="ml-2 font-semibold underline" @click="market.loadTopMarkets(market.topPage)">Retry</button>
    </div>
    <template v-else>
      <CoinTable :rows="rows" empty-hint="No coins match your search." />

      <div v-if="!searching" class="flex items-center justify-between">
        <p class="text-xs text-muted-foreground">Page {{ market.topPage }} · top coins by market cap</p>
        <div class="flex items-center gap-2">
          <button
            class="inline-flex items-center gap-1 rounded-lg border border-border bg-card px-3 py-2 text-sm font-semibold transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-40"
            :disabled="market.topPage <= 1 || market.topLoading"
            @click="goToPage(market.topPage - 1)"
          >
            <ChevronLeft class="h-4 w-4" /> Prev
          </button>
          <button
            class="inline-flex items-center gap-1 rounded-lg border border-border bg-card px-3 py-2 text-sm font-semibold transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-40"
            :disabled="!market.topHasMore || market.topLoading"
            @click="goToPage(market.topPage + 1)"
          >
            <Loader2 v-if="market.topLoading" class="h-4 w-4 animate-spin" /> Next <ChevronRight class="h-4 w-4" />
          </button>
        </div>
      </div>
    </template>
  </div>
</template>
