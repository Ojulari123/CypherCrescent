<script setup lang="ts">
import { Wallet, TrendingUp, TrendingDown, Trophy, AlertTriangle, Plus, Pencil, Trash2, Loader2, ArrowUp, ArrowDown, ChevronsUpDown } from 'lucide-vue-next'
import { fmtUsd, fmtNum, fmtPrice, UP, DOWN } from '~/utils/format'
import { RANGES, RANGE_LABEL, coinColor } from '~/utils/coins'

const portfolio = usePortfolioStore()
const ui = useUiStore()

const range = ref<'24h' | '7d' | '30d'>('7d')
const donutActive = ref<string | null>(null)

const dash = computed(() => portfolio.dashboard)

const filteredHoldings = computed(() => {
  const q = ui.query.toLowerCase()
  const list = portfolio.holdings
  return q ? list.filter((h) => `${h.name ?? ''}${h.symbol ?? ''}${h.coin_slug}`.toLowerCase().includes(q)) : list
})

// Sort holdings by current value or P/L (largest first by default).
const holdingSort = ref<'value' | 'pl'>('value')
const holdingDir = ref<'asc' | 'desc'>('desc')
function setHoldingSort(key: 'value' | 'pl') {
  if (holdingSort.value === key) holdingDir.value = holdingDir.value === 'asc' ? 'desc' : 'asc'
  else {
    holdingSort.value = key
    holdingDir.value = 'desc'
  }
}
const sortedHoldings = computed(() => {
  const arr = [...filteredHoldings.value]
  arr.sort((a, b) => {
    const av = a[holdingSort.value]
    const bv = b[holdingSort.value]
    if (av == null && bv == null) return 0
    if (av == null) return 1
    if (bv == null) return -1
    return holdingDir.value === 'asc' ? av - bv : bv - av
  })
  return arr
})

const allocation = computed(() =>
  portfolio.holdings
    .map((h) => ({ label: h.symbol || h.coin_slug.toUpperCase(), value: h.value ?? 0, color: coinColor(h.coin_slug) }))
    .filter((a) => a.value > 0)
    .sort((a, b) => b.value - a.value),
)
const totalValue = computed(() => dash.value?.total_value ?? 0)
const activeSlice = computed(() => allocation.value.find((a) => a.label === donutActive.value))

const chartColor = computed(() => {
  const s = portfolio.series
  return s.length > 1 && s[s.length - 1] >= s[0] ? UP : DOWN
})
const periodChange = computed(() => {
  const s = portfolio.series
  return s.length > 1 ? ((s[s.length - 1] - s[0]) / s[0]) * 100 : 0
})

async function refresh() {
  await portfolio.loadDashboard()
  await portfolio.loadPerformance(range.value)
}

watch(range, (r) => portfolio.loadPerformance(r))
onMounted(refresh)
</script>

<template>
  <div class="space-y-5">
    <div>
      <h1 class="text-xl font-bold md:text-2xl">Dashboard</h1>
      <p class="text-sm text-muted-foreground">Portfolio overview &amp; performance</p>
    </div>

    <!-- loading -->
    <div v-if="portfolio.loading && !dash" class="flex items-center justify-center rounded-xl border border-border bg-card py-20 text-muted-foreground">
      <Loader2 class="h-6 w-6 animate-spin" /> <span class="ml-2 text-sm">Loading your portfolio…</span>
    </div>

    <!-- error -->
    <div v-else-if="portfolio.error" class="rounded-xl border border-red-500/30 bg-red-500/5 p-5 text-sm text-red-500">
      {{ portfolio.error }}
      <button class="ml-2 font-semibold underline" @click="refresh">Retry</button>
    </div>

    <template v-else-if="dash">
      <!-- stat cards -->
      <div class="grid grid-cols-2 gap-3 xl:grid-cols-4">
        <StatCard label="Total portfolio value" :value="fmtUsd(dash.total_value)" accent="#3861fb">
          <template #icon><Wallet class="h-4 w-4" /></template>
          <template #sub><span class="text-muted-foreground">Cost {{ fmtUsd(dash.total_cost, 0) }}</span></template>
        </StatCard>
        <StatCard label="Total profit / loss" :value="fmtUsd(dash.total_pl)" :accent="dash.total_pl >= 0 ? UP : DOWN">
          <template #icon><component :is="dash.total_pl >= 0 ? TrendingUp : TrendingDown" class="h-4 w-4" /></template>
          <template #sub><ChangeBadge :value="dash.total_pl_percent" /></template>
        </StatCard>
        <StatCard label="Top performer" :value="dash.top_performer?.name || dash.top_performer?.coin_slug?.toUpperCase() || '—'" accent="#f59e0b">
          <template #icon><Trophy class="h-4 w-4" /></template>
          <template #sub><ChangeBadge v-if="dash.top_performer" :value="dash.top_performer.pl_percent" /></template>
        </StatCard>
        <StatCard label="Worst performer" :value="dash.worst_performer?.name || dash.worst_performer?.coin_slug?.toUpperCase() || '—'" accent="#ef4444">
          <template #icon><AlertTriangle class="h-4 w-4" /></template>
          <template #sub><ChangeBadge v-if="dash.worst_performer" :value="dash.worst_performer.pl_percent" /></template>
        </StatCard>
      </div>

      <!-- chart + allocation -->
      <div class="grid grid-cols-1 gap-3 lg:grid-cols-3">
        <div class="rounded-xl border border-border bg-card p-5 lg:col-span-2">
          <div class="mb-4 flex flex-wrap items-start justify-between gap-3">
            <div>
              <p class="text-xs text-muted-foreground">Portfolio value</p>
              <p class="text-2xl font-bold tabular-nums">{{ fmtUsd(dash.total_value) }}</p>
              <div class="mt-0.5 text-sm"><ChangeBadge :value="periodChange" /> <span class="text-muted-foreground">past {{ RANGE_LABEL[range] }}</span></div>
            </div>
            <div class="flex gap-1 rounded-lg bg-muted p-1">
              <button v-for="r in RANGES" :key="r" class="rounded-md px-2.5 py-1 text-xs font-semibold transition-all" :class="range === r ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'" @click="range = r">
                {{ RANGE_LABEL[r] }}
              </button>
            </div>
          </div>
          <div v-if="portfolio.seriesLoading" class="flex h-[250px] items-center justify-center text-muted-foreground"><Loader2 class="h-5 w-5 animate-spin" /></div>
          <div v-else-if="portfolio.series.length" class="text-foreground/70"><AreaChart :values="portfolio.series" :color="chartColor" :height="250" /></div>
          <div v-else class="flex h-[250px] items-center justify-center text-sm text-muted-foreground">No price history available.</div>
        </div>

        <div class="rounded-xl border border-border bg-card p-5">
          <p class="mb-4 text-sm font-semibold">Allocation</p>
          <template v-if="allocation.length">
            <div class="relative flex items-center justify-center">
              <DonutChart :data="allocation" :size="180" :active="donutActive" @hover="donutActive = $event" />
              <div class="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center">
                <span class="text-[11px] text-muted-foreground">{{ activeSlice ? activeSlice.label : 'Total' }}</span>
                <span class="text-lg font-bold tabular-nums">{{ fmtUsd(activeSlice ? activeSlice.value : totalValue, 0) }}</span>
              </div>
            </div>
            <div class="mt-4 space-y-1.5">
              <div v-for="a in allocation" :key="a.label" class="flex cursor-default items-center justify-between rounded-md px-1 py-0.5 text-sm transition-colors hover:bg-muted" @mouseenter="donutActive = a.label" @mouseleave="donutActive = null">
                <span class="flex items-center gap-2"><span class="h-2.5 w-2.5 rounded-full" :style="{ background: a.color }" /><span class="font-medium">{{ a.label }}</span></span>
                <span class="tabular-nums text-muted-foreground">{{ totalValue ? ((a.value / totalValue) * 100).toFixed(1) : '0' }}%</span>
              </div>
            </div>
          </template>
          <p v-else class="py-10 text-center text-sm text-muted-foreground">No holdings yet.</p>
        </div>
      </div>

      <!-- holdings table -->
      <div class="rounded-xl border border-border bg-card">
        <div class="flex items-center justify-between p-5 pb-3">
          <p class="text-sm font-bold">Holdings <span class="text-muted-foreground">({{ filteredHoldings.length }})</span></p>
          <button class="inline-flex items-center gap-1 rounded-lg bg-muted px-2.5 py-1 text-xs font-semibold transition-colors hover:bg-primary hover:text-primary-foreground" @click="ui.openAddHolding()">
            <Plus class="h-3.5 w-3.5" /> Add
          </button>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full min-w-[720px] text-sm">
            <thead>
              <tr class="border-y border-border text-left text-xs text-muted-foreground">
                <th class="px-5 py-2.5">Asset</th>
                <th class="px-3 py-2.5 text-right">Price</th>
                <th class="px-3 py-2.5 text-right">Holdings</th>
                <th class="hidden px-3 py-2.5 text-right lg:table-cell">Buy price</th>
                <th class="px-3 py-2.5 text-right" :aria-sort="holdingSort === 'value' ? (holdingDir === 'asc' ? 'ascending' : 'descending') : 'none'">
                  <button class="group/s ml-auto inline-flex items-center gap-1 transition-colors hover:text-foreground" :class="holdingSort === 'value' ? 'font-semibold text-foreground' : ''" @click="setHoldingSort('value')">
                    Value
                    <ArrowUp v-if="holdingSort === 'value' && holdingDir === 'asc'" class="h-3.5 w-3.5" />
                    <ArrowDown v-else-if="holdingSort === 'value'" class="h-3.5 w-3.5" />
                    <ChevronsUpDown v-else class="h-3.5 w-3.5 opacity-0 transition-opacity group-hover/s:opacity-50" />
                  </button>
                </th>
                <th class="px-3 py-2.5 text-right" :aria-sort="holdingSort === 'pl' ? (holdingDir === 'asc' ? 'ascending' : 'descending') : 'none'">
                  <button class="group/s ml-auto inline-flex items-center gap-1 transition-colors hover:text-foreground" :class="holdingSort === 'pl' ? 'font-semibold text-foreground' : ''" @click="setHoldingSort('pl')">
                    P/L
                    <ArrowUp v-if="holdingSort === 'pl' && holdingDir === 'asc'" class="h-3.5 w-3.5" />
                    <ArrowDown v-else-if="holdingSort === 'pl'" class="h-3.5 w-3.5" />
                    <ChevronsUpDown v-else class="h-3.5 w-3.5 opacity-0 transition-opacity group-hover/s:opacity-50" />
                  </button>
                </th>
                <th class="px-5 py-2.5"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="h in sortedHoldings" :key="h.id" class="group border-b border-border/60 transition-colors last:border-0 hover:bg-muted/50">
                <td class="px-5 py-3">
                  <NuxtLink :to="`/coins/${h.coin_slug}`" class="flex items-center gap-3">
                    <CoinIcon :slug="h.coin_slug" :symbol="h.symbol" :image="h.image" :size="30" />
                    <span class="leading-tight">
                      <span class="block font-semibold group-hover:text-primary">{{ h.name || h.coin_slug }}</span>
                      <span class="block text-xs uppercase text-muted-foreground">{{ h.symbol }}</span>
                    </span>
                  </NuxtLink>
                </td>
                <td class="px-3 py-3 text-right font-medium tabular-nums">{{ h.current_price != null ? fmtPrice(h.current_price) : '—' }}</td>
                <td class="px-3 py-3 text-right tabular-nums">
                  <span class="block">{{ fmtNum(h.quantity) }}</span>
                  <span class="block text-xs uppercase text-muted-foreground">{{ h.symbol }}</span>
                </td>
                <td class="hidden px-3 py-3 text-right tabular-nums text-muted-foreground lg:table-cell">{{ fmtUsd(h.buy_price) }}</td>
                <td class="px-3 py-3 text-right font-semibold tabular-nums">{{ h.value != null ? fmtUsd(h.value) : '—' }}</td>
                <td class="px-3 py-3 text-right">
                  <ChangeBadge :value="h.pl_percent" class="justify-end" />
                  <span v-if="h.pl != null" class="block text-xs tabular-nums" :style="{ color: h.pl >= 0 ? UP : DOWN }">{{ h.pl >= 0 ? '+' : '' }}{{ fmtUsd(h.pl) }}</span>
                </td>
                <td class="px-5 py-3">
                  <div class="flex justify-end gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                    <button class="rounded-lg bg-muted p-1.5 transition-colors hover:bg-primary hover:text-primary-foreground" aria-label="Edit" @click="ui.openEditHolding(h)"><Pencil class="h-3.5 w-3.5" /></button>
                    <button class="rounded-lg bg-muted p-1.5 transition-colors hover:bg-red-500 hover:text-white" aria-label="Delete" @click="ui.askDeleteHolding(h.id)"><Trash2 class="h-3.5 w-3.5" /></button>
                  </div>
                </td>
              </tr>
              <tr v-if="!filteredHoldings.length">
                <td colspan="7" class="px-5 py-12 text-center">
                  <p class="text-sm text-muted-foreground">{{ ui.query ? 'No holdings match your search.' : 'No holdings yet.' }}</p>
                  <button v-if="!ui.query" class="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground" @click="ui.openAddHolding()">
                    <Plus class="h-4 w-4" /> Add your first holding
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
