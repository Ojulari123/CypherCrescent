<script setup lang="ts">
import { Star, Plus, Loader2 } from 'lucide-vue-next'

const watchlist = useWatchlistStore()
const ui = useUiStore()

onMounted(() => watchlist.load())

const rows = computed(() => {
  const q = ui.query.toLowerCase().trim()
  const mapped = watchlist.items.map((i) => ({
    id: i.coin_slug,
    symbol: i.symbol,
    name: i.name,
    image: i.image,
    current_price: i.current_price,
    market_cap: i.market_cap,
    price_change_percentage_1h: i.price_change_percentage_1h,
    price_change_percentage_24h: i.price_change_percentage_24h,
    price_change_percentage_7d: i.price_change_percentage_7d,
  }))
  return q ? mapped.filter((c) => `${c.name ?? ''}${c.symbol ?? ''}${c.id}`.toLowerCase().includes(q)) : mapped
})
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-end justify-between">
      <div>
        <h1 class="text-xl font-bold md:text-2xl">Watchlist</h1>
        <p class="text-sm text-muted-foreground">{{ watchlist.items.length }} coin{{ watchlist.items.length === 1 ? '' : 's' }} you're tracking</p>
      </div>
      <NuxtLink to="/markets" class="inline-flex items-center gap-1 rounded-lg border border-border bg-card px-3 py-2 text-sm font-semibold transition-colors hover:bg-muted">
        <Plus class="h-4 w-4" /> Browse markets
      </NuxtLink>
    </div>

    <div v-if="watchlist.loading && !watchlist.items.length" class="flex items-center justify-center rounded-xl border border-border bg-card py-20 text-muted-foreground">
      <Loader2 class="h-6 w-6 animate-spin" /> <span class="ml-2 text-sm">Loading watchlist…</span>
    </div>
    <div v-else-if="!watchlist.items.length" class="rounded-xl border border-dashed border-border py-16 text-center">
      <Star class="mx-auto mb-2 h-7 w-7 text-muted-foreground" />
      <p class="font-medium">Your watchlist is empty</p>
      <p class="mt-1 text-sm text-muted-foreground">Star coins in Markets to track them here.</p>
      <NuxtLink to="/markets" class="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground">
        <Plus class="h-4 w-4" /> Browse markets
      </NuxtLink>
    </div>
    <CoinTable v-else :rows="rows" empty-hint="No watched coins match your search." />
  </div>
</template>
