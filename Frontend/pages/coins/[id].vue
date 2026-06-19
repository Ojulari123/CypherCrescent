<script setup lang="ts">
import { ChevronRight, Star, Plus, Pencil, Trash2, ArrowRightLeft, Loader2 } from 'lucide-vue-next'
import { fmtUsd, fmtPrice, fmtNum, fmtCompact, UP, DOWN } from '~/utils/format'
import { RANGES, RANGE_LABEL } from '~/utils/coins'

const route = useRoute()
const market = useMarketStore()
const portfolio = usePortfolioStore()
const watchlist = useWatchlistStore()
const ui = useUiStore()

const slug = computed(() => String(route.params.id))
const range = ref<'24h' | '7d' | '30d'>('7d')
const points = ref<number[]>([])
const chartLoading = ref(false)
const coinLoading = ref(true)

const coin = computed(() => market.bySlug(slug.value))
const watched = computed(() => watchlist.isWatched(slug.value))
const position = computed(() => portfolio.holdings.find((h) => h.coin_slug === slug.value))

const totalCap = computed(() => market.coins.reduce((s, c) => s + (c.market_cap ?? 0), 0))
const dominance = computed(() => (totalCap.value && coin.value?.market_cap ? (coin.value.market_cap / totalCap.value) * 100 : null))
const prevPrice = computed(() => {
  const c = coin.value
  if (!c?.current_price || c.price_change_percentage_24h == null) return null
  return c.current_price / (1 + c.price_change_percentage_24h / 100)
})

const rangeChange = computed(() => (points.value.length > 1 ? ((points.value[points.value.length - 1] - points.value[0]) / points.value[0]) * 100 : 0))

// Converter (two-way)
const coinAmt = ref('1')
const usdAmt = ref('')
watch(coin, (c) => { if (c?.current_price) usdAmt.value = String(c.current_price) }, { immediate: true })
function onCoinAmt(v: string) {
  coinAmt.value = v
  const n = parseFloat(v)
  usdAmt.value = isNaN(n) || !coin.value?.current_price ? '' : (n * coin.value.current_price).toFixed(2)
}
function onUsdAmt(v: string) {
  usdAmt.value = v
  const n = parseFloat(v)
  coinAmt.value = isNaN(n) || !coin.value?.current_price ? '' : (n / coin.value.current_price).toFixed(6)
}

async function loadChart() {
  chartLoading.value = true
  try {
    const res = await market.getChart(slug.value, range.value)
    points.value = (res.points ?? []).map((p) => p.price)
  } catch {
    points.value = []
  } finally {
    chartLoading.value = false
  }
}

async function toggleWatch() {
  const was = watched.value
  try {
    await watchlist.toggle(slug.value)
    ui.toast(was ? 'Removed from watchlist' : 'Added to watchlist')
  } catch (e: any) {
    ui.toast(e?.data?.detail || 'Watchlist update failed')
  }
}

function addHolding() {
  if (position.value) ui.openEditHolding(position.value)
  else ui.openAddHolding()
}

watch(range, loadChart)

onMounted(async () => {
  await market.ensureCoins([slug.value])
  if (!portfolio.dashboard) await portfolio.loadDashboard()
  coinLoading.value = false
  loadChart()
})
</script>

<template>
  <div>
    <CoinDetailSkeleton v-if="coinLoading && !coin" />

    <div v-else-if="!coin" class="rounded-xl border border-border bg-card py-20 text-center">
      <p class="text-sm text-muted-foreground">We couldn't load market data for “{{ slug }}”.</p>
      <NuxtLink to="/markets" class="mt-3 inline-block text-sm font-semibold text-primary hover:underline">← Back to markets</NuxtLink>
    </div>

    <div v-else class="space-y-5">
      <!-- breadcrumb -->
      <div class="flex items-center gap-1 text-xs text-muted-foreground">
        <NuxtLink to="/markets" class="hover:text-foreground">Markets</NuxtLink>
        <ChevronRight class="h-3 w-3" />
        <span class="font-medium text-foreground">{{ coin.name }}</span>
      </div>

      <div class="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_340px]">
        <!-- main -->
        <div class="space-y-5">
          <div class="flex flex-wrap items-center justify-between gap-4">
            <div class="flex items-center gap-3">
              <CoinIcon :slug="coin.id" :symbol="coin.symbol" :image="coin.image" :size="40" />
              <div>
                <div class="flex items-center gap-2">
                  <h1 class="text-xl font-bold md:text-2xl">{{ coin.name }}</h1>
                  <span class="rounded bg-muted px-1.5 py-0.5 text-xs font-semibold text-muted-foreground">{{ coin.symbol }}</span>
                </div>
              </div>
            </div>
            <button class="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-sm font-semibold transition-colors hover:bg-muted" @click="toggleWatch">
              <Star class="h-4 w-4" :class="watched ? 'fill-amber-400 text-amber-400' : ''" />
              {{ watched ? 'Watching' : 'Watchlist' }}
            </button>
          </div>

          <div class="flex items-end gap-3">
            <span class="text-3xl font-bold tabular-nums md:text-4xl">{{ coin.current_price != null ? fmtPrice(coin.current_price) : '—' }}</span>
            <ChangeBadge :value="coin.price_change_percentage_24h" class="mb-1.5 text-base" />
            <span class="mb-1.5 text-sm text-muted-foreground">(24h)</span>
          </div>

          <!-- chart -->
          <div class="rounded-xl border border-border bg-card p-5">
            <div class="mb-3 flex items-center justify-between">
              <p class="text-sm font-bold">{{ coin.name }} to USD Chart</p>
              <div class="flex gap-1 rounded-lg bg-muted p-1">
                <button v-for="r in RANGES" :key="r" class="rounded-md px-3 py-1 text-xs font-semibold transition-all" :class="range === r ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'" @click="range = r">
                  {{ RANGE_LABEL[r] }}
                </button>
              </div>
            </div>
            <div v-if="chartLoading" class="flex h-[300px] items-center justify-center text-muted-foreground"><Loader2 class="h-5 w-5 animate-spin" /></div>
            <div v-else-if="points.length" class="text-foreground/70"><AreaChart :values="points" :color="rangeChange >= 0 ? UP : DOWN" :height="300" /></div>
            <div v-else class="flex h-[300px] items-center justify-center text-sm text-muted-foreground">No price history available.</div>
          </div>

          <!-- statistics (only what the API provides) -->
          <div class="rounded-xl border border-border bg-card p-5">
            <h2 class="mb-3 text-lg font-bold">{{ coin.name }} Market Stats</h2>
            <div class="flex items-center justify-between border-b border-border py-3"><span class="text-sm text-muted-foreground">Current Price</span><span class="text-sm font-semibold tabular-nums">{{ coin.current_price != null ? fmtPrice(coin.current_price) : '—' }}</span></div>
            <div class="flex items-center justify-between border-b border-border py-3"><span class="text-sm text-muted-foreground">Market Cap</span><span class="text-sm font-semibold tabular-nums">{{ coin.market_cap != null ? fmtCompact(coin.market_cap) : '—' }}</span></div>
            <div class="flex items-center justify-between border-b border-border py-3"><span class="text-sm text-muted-foreground">24h Change</span><ChangeBadge :value="coin.price_change_percentage_24h" /></div>
            <div class="flex items-center justify-between border-b border-border py-3"><span class="text-sm text-muted-foreground">Market Dominance <span class="text-[11px]">(of tracked)</span></span><span class="text-sm font-semibold tabular-nums">{{ dominance != null ? dominance.toFixed(2) + '%' : '—' }}</span></div>
            <div class="flex items-center justify-between py-3"><span class="text-sm text-muted-foreground">Symbol</span><span class="text-sm font-semibold uppercase">{{ coin.symbol }}</span></div>
          </div>
        </div>

        <!-- right rail -->
        <div class="space-y-4">
          <div v-if="position" class="rounded-xl border border-border bg-card p-4">
            <p class="mb-3 text-sm font-bold">Your position</p>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between"><span class="text-muted-foreground">Holdings</span><span class="font-semibold tabular-nums">{{ fmtNum(position.quantity) }} {{ coin.symbol }}</span></div>
              <div class="flex justify-between"><span class="text-muted-foreground">Value</span><span class="font-semibold tabular-nums">{{ position.value != null ? fmtUsd(position.value) : '—' }}</span></div>
              <div class="flex justify-between"><span class="text-muted-foreground">Avg buy</span><span class="font-semibold tabular-nums">{{ fmtPrice(position.buy_price) }}</span></div>
              <div class="flex justify-between"><span class="text-muted-foreground">Profit / Loss</span><span class="text-right"><ChangeBadge :value="position.pl_percent" class="justify-end" /><span v-if="position.pl != null" class="block text-xs tabular-nums" :style="{ color: position.pl >= 0 ? UP : DOWN }">{{ position.pl >= 0 ? '+' : '' }}{{ fmtUsd(position.pl) }}</span></span></div>
            </div>
            <div class="mt-3 grid grid-cols-2 gap-2">
              <button class="inline-flex items-center justify-center gap-1.5 rounded-lg bg-muted py-2 text-sm font-semibold transition-colors hover:bg-primary hover:text-primary-foreground" @click="ui.openEditHolding(position)"><Pencil class="h-3.5 w-3.5" /> Edit</button>
              <button class="inline-flex items-center justify-center gap-1.5 rounded-lg bg-muted py-2 text-sm font-semibold transition-colors hover:bg-red-500 hover:text-white" @click="ui.askDeleteHolding(position.id)"><Trash2 class="h-3.5 w-3.5" /> Delete</button>
            </div>
          </div>
          <button v-else class="flex w-full items-center justify-center gap-2 rounded-xl bg-primary py-3 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90" @click="addHolding">
            <Plus class="h-4 w-4" /> Add {{ coin.symbol }} to portfolio
          </button>

          <!-- price performance -->
          <div v-if="prevPrice != null" class="rounded-xl border border-border bg-card p-4">
            <p class="mb-3 text-sm font-bold">Price Performance (24h)</p>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between"><span class="text-muted-foreground">Price 24h ago</span><span class="font-semibold tabular-nums">{{ fmtPrice(prevPrice) }}</span></div>
              <div class="flex justify-between"><span class="text-muted-foreground">Current</span><span class="font-semibold tabular-nums">{{ fmtPrice(coin.current_price!) }}</span></div>
              <div class="flex justify-between"><span class="text-muted-foreground">Change</span><ChangeBadge :value="coin.price_change_percentage_24h" /></div>
            </div>
          </div>

          <!-- converter -->
          <div class="rounded-xl border border-border bg-card p-4">
            <p class="mb-3 flex items-center gap-1.5 text-sm font-bold"><ArrowRightLeft class="h-4 w-4 text-primary" /> {{ coin.symbol }} to USD Converter</p>
            <div class="space-y-2">
              <div class="flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2.5">
                <CoinIcon :slug="coin.id" :symbol="coin.symbol" :image="coin.image" :size="22" />
                <input :value="coinAmt" type="number" inputmode="decimal" class="w-full bg-transparent text-sm font-semibold tabular-nums outline-none" @input="onCoinAmt(($event.target as HTMLInputElement).value)" />
                <span class="text-xs font-semibold text-muted-foreground">{{ coin.symbol }}</span>
              </div>
              <div class="flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2.5">
                <span class="flex h-[22px] w-[22px] items-center justify-center rounded-full bg-emerald-500 text-[11px] font-bold text-white">$</span>
                <input :value="usdAmt" type="number" inputmode="decimal" class="w-full bg-transparent text-sm font-semibold tabular-nums outline-none" @input="onUsdAmt(($event.target as HTMLInputElement).value)" />
                <span class="text-xs font-semibold text-muted-foreground">USD</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
