<script setup lang="ts">
import { X } from 'lucide-vue-next'
import { fmtUsd, fmtPrice } from '~/utils/format'

const ui = useUiStore()
const market = useMarketStore()
const portfolio = usePortfolioStore()

const open = computed(() => ui.holdingModal != null)
const editing = computed(() => ui.holdingModal?.mode === 'edit')

const slug = ref('bitcoin')
const qty = ref('')
const buy = ref('')
const touched = ref(false)
const apiError = ref('')

const available = computed(() => {
  const held = new Set(portfolio.heldSlugs)
  const list = market.coins.filter((c) => !held.has(c.id) || c.id === slug.value)
  return list.length ? list : market.coins
})

const coin = computed(() => market.bySlug(slug.value))
const q = computed(() => parseFloat(qty.value))
const b = computed(() => parseFloat(buy.value))
const qErr = computed(() => (touched.value && (isNaN(q.value) || q.value <= 0) ? 'Quantity must be greater than 0' : ''))
const bErr = computed(() => (touched.value && (isNaN(b.value) || b.value <= 0) ? 'Buy price must be greater than 0' : ''))
const valid = computed(() => !qErr.value && !bErr.value && !isNaN(q.value) && !isNaN(b.value))

const price = computed(() => coin.value?.current_price ?? 0)
const cost = computed(() => (!isNaN(q.value) && !isNaN(b.value) ? q.value * b.value : 0))
const marketValue = computed(() => (!isNaN(q.value) ? q.value * price.value : 0))

watch(
  () => ui.holdingModal,
  (m) => {
    apiError.value = ''
    touched.value = false
    if (m?.mode === 'edit') {
      slug.value = m.holding.coin_slug
      qty.value = String(m.holding.quantity)
      buy.value = String(m.holding.buy_price)
    } else if (m?.mode === 'add') {
      const firstFree = market.coins.find((c) => !portfolio.heldSlugs.includes(c.id))
      slug.value = firstFree?.id ?? market.coins[0]?.id ?? 'bitcoin'
      qty.value = ''
      buy.value = ''
    }
  },
)

async function submit() {
  touched.value = true
  apiError.value = ''
  if (isNaN(q.value) || q.value <= 0 || isNaN(b.value) || b.value <= 0) return
  try {
    if (ui.holdingModal?.mode === 'edit') {
      await portfolio.updateHolding(ui.holdingModal.holding.id, { quantity: q.value, buy_price: b.value })
      ui.toast(`Updated ${coin.value?.symbol ?? slug.value}`)
    } else {
      await portfolio.addHolding({ coin_slug: slug.value, quantity: q.value, buy_price: b.value })
      ui.toast(`Added ${coin.value?.symbol ?? slug.value} to portfolio`)
    }
    ui.closeHoldingModal()
  } catch (e: any) {
    apiError.value = e?.data?.detail || 'Something went wrong. Please try again.'
  }
}
</script>

<template>
  <Transition name="fade">
    <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm" @click="ui.closeHoldingModal()">
      <div class="w-full max-w-md overflow-y-auto max-h-[90dvh] rounded-xl border border-border bg-card p-6 shadow-2xl" role="dialog" aria-modal="true" @click.stop>
        <div class="mb-5 flex items-center justify-between">
          <h3 class="text-lg font-bold">{{ editing ? 'Edit holding' : 'Add holding' }}</h3>
          <button class="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground" aria-label="Close" @click="ui.closeHoldingModal()">
            <X class="h-5 w-5" />
          </button>
        </div>

        <label class="mb-1.5 block text-xs font-medium text-muted-foreground">Coin</label>
        <div class="mb-4 flex items-center gap-3 rounded-lg border border-border bg-background p-2.5" :class="editing ? 'opacity-70' : ''">
          <CoinIcon :slug="slug" :symbol="coin?.symbol" :image="coin?.image" :size="30" />
          <select v-model="slug" :disabled="editing" class="min-w-0 flex-1 bg-transparent text-sm font-medium outline-none disabled:cursor-not-allowed">
            <option v-for="c in available" :key="c.id" :value="c.id">{{ c.name }} ({{ c.symbol }})</option>
          </select>
          <span class="shrink-0 whitespace-nowrap text-sm font-semibold tabular-nums">{{ price ? fmtPrice(price) : '—' }}</span>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="mb-1.5 block text-xs font-medium text-muted-foreground">Quantity</label>
            <input
              v-model="qty" type="number" inputmode="decimal" min="0" step="any" placeholder="0.00" autofocus
              class="w-full rounded-lg border bg-background px-3 py-2.5 text-sm font-semibold tabular-nums outline-none focus:ring-2"
              :class="qErr ? 'border-red-500 focus:ring-red-500/25' : 'border-border focus:ring-primary/25'"
              @blur="touched = true" @keydown.enter="submit"
            />
          </div>
          <div>
            <label class="mb-1.5 block text-xs font-medium text-muted-foreground">Buy price (USD)</label>
            <input
              v-model="buy" type="number" inputmode="decimal" min="0" step="any" placeholder="0.00"
              class="w-full rounded-lg border bg-background px-3 py-2.5 text-sm font-semibold tabular-nums outline-none focus:ring-2"
              :class="bErr ? 'border-red-500 focus:ring-red-500/25' : 'border-border focus:ring-primary/25'"
              @blur="touched = true" @keydown.enter="submit"
            />
          </div>
        </div>
        <p v-if="qErr || bErr" class="mt-2 text-xs font-medium text-red-500">{{ qErr || bErr }}</p>

        <div class="my-4 space-y-1.5 rounded-lg bg-muted px-3.5 py-3 text-sm">
          <div class="flex justify-between"><span class="text-muted-foreground">Cost basis</span><span class="font-semibold tabular-nums">{{ fmtUsd(cost) }}</span></div>
          <div class="flex justify-between"><span class="text-muted-foreground">Current value</span><span class="font-semibold tabular-nums">{{ fmtUsd(marketValue) }}</span></div>
          <div class="flex justify-between"><span class="text-muted-foreground">Unrealized P/L</span><ChangeBadge :value="cost > 0 ? ((marketValue - cost) / cost) * 100 : 0" /></div>
        </div>

        <p v-if="apiError" class="mb-3 rounded-lg bg-red-500/10 px-3 py-2 text-xs font-medium text-red-500">{{ apiError }}</p>

        <button
          :disabled="!valid || portfolio.mutating"
          class="w-full rounded-lg bg-primary py-3 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-50 active:scale-[0.99]"
          @click="submit"
        >
          {{ portfolio.mutating ? 'Saving…' : editing ? 'Save changes' : 'Add holding' }}
        </button>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
