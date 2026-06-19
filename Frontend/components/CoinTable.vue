<script setup lang="ts">
import { Star, ArrowUp, ArrowDown, ChevronsUpDown } from 'lucide-vue-next'
import { fmtPrice, fmtCompact } from '~/utils/format'

interface Row {
  id: string
  symbol?: string | null
  name?: string | null
  image?: string | null
  market_cap_rank?: number | null
  current_price: number | null
  market_cap: number | null
  price_change_percentage_1h?: number | null
  price_change_percentage_24h: number | null
  price_change_percentage_7d?: number | null
}

type SortKey =
  | 'market_cap'
  | 'current_price'
  | 'price_change_percentage_1h'
  | 'price_change_percentage_24h'
  | 'price_change_percentage_7d'

const props = withDefaults(defineProps<{ rows: Row[]; emptyHint?: string }>(), { emptyHint: 'No coins to show.' })

const watchlist = useWatchlistStore()
const portfolio = usePortfolioStore()
const ui = useUiStore()

// Sortable numeric columns (Price, 1h/24h/7d %, Market Cap). Name stays fixed.
const numCols: Array<{ key: SortKey; label: string; kind: 'price' | 'pct' | 'cap'; mobileHide?: boolean }> = [
  { key: 'current_price', label: 'Price', kind: 'price' },
  { key: 'price_change_percentage_1h', label: '1h %', kind: 'pct', mobileHide: true },
  { key: 'price_change_percentage_24h', label: '24h %', kind: 'pct' },
  { key: 'price_change_percentage_7d', label: '7d %', kind: 'pct', mobileHide: true },
  { key: 'market_cap', label: 'Market Cap', kind: 'cap', mobileHide: true },
]

const sortKey = ref<SortKey>('market_cap')
const sortDir = ref<'asc' | 'desc'>('desc')

function setSort(key: SortKey) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'desc'
  }
}

const sortedRows = computed(() => {
  const arr = [...props.rows]
  arr.sort((a, b) => {
    const av = a[sortKey.value] as number | null | undefined
    const bv = b[sortKey.value] as number | null | undefined
    // Coins missing this metric always sort to the bottom, regardless of direction.
    if (av == null && bv == null) return 0
    if (av == null) return 1
    if (bv == null) return -1
    return sortDir.value === 'asc' ? av - bv : bv - av
  })
  return arr
})

async function toggleWatch(slug: string) {
  const watched = watchlist.isWatched(slug)
  try {
    await watchlist.toggle(slug)
    ui.toast(watched ? 'Removed from watchlist' : 'Added to watchlist')
  } catch (e: any) {
    ui.toast(e?.data?.detail || 'Watchlist update failed')
  }
}
</script>

<template>
  <div class="overflow-hidden rounded-xl border border-border bg-card">
    <div class="overflow-x-auto">
      <table class="w-full min-w-[360px] text-sm">
        <thead>
          <tr class="border-b border-border text-left text-xs text-muted-foreground">
            <th class="w-8 px-4 py-3"></th>
            <th class="px-2 py-3">#</th>
            <th class="px-3 py-3">Name</th>
            <th
              v-for="col in numCols"
              :key="col.key"
              class="px-3 py-3 text-right"
              :class="col.mobileHide ? 'hidden sm:table-cell' : ''"
              :aria-sort="sortKey === col.key ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'"
            >
              <button
                class="group/sort ml-auto inline-flex items-center gap-1 transition-colors hover:text-foreground"
                :class="sortKey === col.key ? 'font-semibold text-foreground' : ''"
                @click="setSort(col.key)"
              >
                <span>{{ col.label }}</span>
                <ArrowUp v-if="sortKey === col.key && sortDir === 'asc'" class="h-3.5 w-3.5" />
                <ArrowDown v-else-if="sortKey === col.key" class="h-3.5 w-3.5" />
                <ChevronsUpDown v-else class="h-3.5 w-3.5 opacity-0 transition-opacity group-hover/sort:opacity-50" />
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, i) in sortedRows" :key="row.id" class="group border-b border-border/60 transition-colors last:border-0 hover:bg-muted/50">
            <td class="px-4 py-3">
              <button aria-label="Toggle watchlist" class="rounded p-1 transition-colors hover:bg-muted" @click="toggleWatch(row.id)">
                <Star class="h-4 w-4 transition-colors" :class="watchlist.isWatched(row.id) ? 'fill-amber-400 text-amber-400' : 'text-muted-foreground'" />
              </button>
            </td>
            <td class="px-2 py-3 text-muted-foreground tabular-nums">{{ row.market_cap_rank ?? i + 1 }}</td>
            <td class="px-3 py-3">
              <NuxtLink :to="`/coins/${row.id}`" class="flex items-center gap-3">
                <CoinIcon :slug="row.id" :symbol="row.symbol" :image="row.image" :size="30" />
                <span class="leading-tight">
                  <span class="block font-semibold group-hover:text-primary">{{ row.name || row.id }}</span>
                  <span class="block text-xs uppercase text-muted-foreground">{{ row.symbol }}</span>
                </span>
                <span v-if="portfolio.heldSlugs.includes(row.id)" class="rounded bg-emerald-500/15 px-1 text-[10px] font-semibold text-emerald-600">HELD</span>
              </NuxtLink>
            </td>
            <td v-for="col in numCols" :key="col.key" class="px-3 py-3 text-right tabular-nums" :class="[col.kind === 'price' ? 'font-semibold' : '', col.mobileHide ? 'hidden sm:table-cell' : '']">
              <template v-if="col.kind === 'price'">{{ row.current_price != null ? fmtPrice(row.current_price) : '—' }}</template>
              <ChangeBadge v-else-if="col.kind === 'pct'" :value="(row[col.key] as number | null) ?? null" class="justify-end" />
              <template v-else>{{ row.market_cap != null ? fmtCompact(row.market_cap) : '—' }}</template>
            </td>
          </tr>
          <tr v-if="!sortedRows.length">
            <td colspan="8" class="px-5 py-12 text-center text-sm text-muted-foreground">{{ emptyHint }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
