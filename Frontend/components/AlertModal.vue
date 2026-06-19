<script setup lang="ts">
import { X, Bell, Loader2 } from 'lucide-vue-next'
import { watchDebounced } from '@vueuse/core'
import { fmtPrice } from '~/utils/format'
import type { PriceAlert } from '~/types/api'

const props = defineProps<{
  coinSlug?: string
  coinName?: string
  currentPrice?: number | null
  // Pass an existing alert to open in edit mode instead of create mode
  alert?: PriceAlert
}>()

const emit = defineEmits<{ close: [] }>()

const alertStore = useAlertStore()
const marketStore = useMarketStore()
const ui = useUiStore()

const isEdit = computed(() => !!props.alert)

// ── Coin selection (only used when no coinSlug prop) ──────────────────────────

const selectedSlug = ref(props.alert?.coin_slug ?? props.coinSlug ?? '')
const selectedName = ref(props.coinName ?? '')
const coinSearch = ref(props.coinName ?? '')
const dropdownOpen = ref(false)
let skipNextSearch = false

watchDebounced(
  coinSearch,
  async (q) => {
    if (props.coinSlug) return  // pre-filled, no search needed
    if (skipNextSearch) { skipNextSearch = false; return }
    if (q.trim().length < 2) { marketStore.searchResults = []; return }
    await marketStore.search(q)
    dropdownOpen.value = true
  },
  { debounce: 300 },
)

function selectResult(r: { id: string; name: string; symbol: string }) {
  selectedSlug.value = r.id
  selectedName.value = r.name
  skipNextSearch = true
  coinSearch.value = r.name
  dropdownOpen.value = false
  marketStore.searchResults = []
  marketStore.ensureCoins([r.id])
}

// ── Current price (from prop or market cache) ─────────────────────────────────

const livePrice = computed(() => {
  if (props.currentPrice != null) return props.currentPrice
  return marketStore.bySlug(selectedSlug.value)?.current_price ?? null
})

// ── Alert config ──────────────────────────────────────────────────────────────

const direction = ref<'above' | 'below'>(props.alert?.direction ?? 'above')
const targetPrice = ref(props.alert ? String(props.alert.target_price) : '')

const canSubmit = computed(() =>
  selectedSlug.value && targetPrice.value && parseFloat(targetPrice.value) > 0,
)

async function submit() {
  if (!canSubmit.value) return
  const price = parseFloat(targetPrice.value)
  try {
    if (isEdit.value && props.alert) {
      await alertStore.update(props.alert.id, price, direction.value)
      ui.toast('Alert updated')
    } else {
      await alertStore.create(selectedSlug.value, price, direction.value)
      ui.toast(`Alert set for ${selectedName.value || selectedSlug.value}`)
    }
    emit('close')
  } catch (e: any) {
    ui.toast(e?.data?.detail || (isEdit.value ? 'Could not update alert' : 'Could not create alert'))
  }
}

function onBackdrop() { emit('close') }
</script>

<template>
  <Transition name="fade">
    <div class="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-4 backdrop-blur-sm sm:items-center" @click="onBackdrop">
      <div
        class="w-full max-w-md overflow-y-auto rounded-xl border border-border bg-card shadow-2xl"
        style="max-height: 90dvh"
        @click.stop
      >
        <!-- header -->
        <div class="flex items-center justify-between border-b border-border px-5 py-4">
          <div class="flex items-center gap-2">
            <Bell class="h-4 w-4 text-primary" />
            <h2 class="text-base font-bold">{{ isEdit ? 'Edit Alert' : 'New Price Alert' }}</h2>
          </div>
          <button class="rounded-lg p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground" @click="emit('close')">
            <X class="h-4 w-4" />
          </button>
        </div>

        <div class="space-y-5 p-5">
          <!-- Coin field -->
          <div>
            <label class="mb-1.5 block text-xs font-semibold text-muted-foreground uppercase tracking-wider">Coin</label>

            <!-- pre-filled (from coin page) -->
            <div v-if="coinSlug" class="flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2.5">
              <CoinIcon :slug="selectedSlug" :symbol="coinName ?? selectedSlug.toUpperCase()" :image="null" :size="22" />
              <span class="text-sm font-semibold">{{ selectedName || selectedSlug }}</span>
            </div>

            <!-- search (from alerts page) -->
            <div v-else class="relative">
              <input
                v-model="coinSearch"
                type="text"
                placeholder="Search by name or symbol…"
                autocomplete="off"
                class="w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-primary/20"
              />
              <div
                v-if="dropdownOpen && marketStore.searchResults.length"
                class="absolute left-0 right-0 top-full z-10 mt-1 overflow-hidden rounded-lg border border-border bg-card shadow-lg"
              >
                <button
                  v-for="r in marketStore.searchResults.slice(0, 6)"
                  :key="r.id"
                  class="flex w-full items-center gap-2.5 px-3 py-2.5 text-left text-sm hover:bg-muted"
                  @click="selectResult(r)"
                >
                  <span class="font-semibold">{{ r.name }}</span>
                  <span class="text-xs text-muted-foreground">{{ r.symbol?.toUpperCase() }}</span>
                  <span v-if="r.market_cap_rank" class="ml-auto text-xs text-muted-foreground">#{{ r.market_cap_rank }}</span>
                </button>
              </div>
            </div>
          </div>

          <!-- current price reference -->
          <div v-if="livePrice != null && selectedSlug" class="rounded-lg bg-muted/50 px-4 py-3 text-sm">
            <span class="text-muted-foreground">Current price:</span>
            <span class="ml-2 font-bold tabular-nums">{{ fmtPrice(livePrice) }}</span>
          </div>

          <!-- direction -->
          <div>
            <label class="mb-1.5 block text-xs font-semibold text-muted-foreground uppercase tracking-wider">Notify me when price is</label>
            <div class="grid grid-cols-2 gap-2">
              <button
                class="rounded-lg border py-2.5 text-sm font-semibold transition-colors"
                :class="direction === 'above'
                  ? 'border-primary bg-primary/10 text-primary'
                  : 'border-border bg-background text-muted-foreground hover:bg-muted'"
                @click="direction = 'above'"
              >
                ↑ Above
              </button>
              <button
                class="rounded-lg border py-2.5 text-sm font-semibold transition-colors"
                :class="direction === 'below'
                  ? 'border-primary bg-primary/10 text-primary'
                  : 'border-border bg-background text-muted-foreground hover:bg-muted'"
                @click="direction = 'below'"
              >
                ↓ Below
              </button>
            </div>
          </div>

          <!-- target price -->
          <div>
            <label class="mb-1.5 block text-xs font-semibold text-muted-foreground uppercase tracking-wider">Target price (USD)</label>
            <div class="flex items-center rounded-lg border border-border bg-background px-3 py-2.5 focus-within:ring-2 focus-within:ring-primary/20">
              <span class="mr-2 text-sm font-semibold text-muted-foreground">$</span>
              <input
                v-model="targetPrice"
                type="number"
                inputmode="decimal"
                min="0.000001"
                step="any"
                placeholder="0.00"
                class="w-full bg-transparent text-sm font-semibold tabular-nums outline-none"
              />
            </div>
          </div>

          <!-- limit hint (only shown when creating) -->
          <p v-if="!isEdit" class="text-xs text-muted-foreground">
            You can have up to 10 active alerts. Triggered alerts don't count.
            <span v-if="alertStore.atLimit" class="font-semibold text-red-500"> Limit reached.</span>
            <span v-else> ({{ 10 - alertStore.activeCount }} remaining)</span>
          </p>
        </div>

        <!-- footer -->
        <div class="border-t border-border px-5 py-4">
          <button
            class="w-full rounded-lg bg-primary py-2.5 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
            :disabled="!canSubmit || alertStore.creating || (!isEdit && alertStore.atLimit)"
            @click="submit"
          >
            <span v-if="alertStore.creating" class="inline-flex items-center gap-2"><Loader2 class="h-4 w-4 animate-spin" /> {{ isEdit ? 'Saving…' : 'Setting alert…' }}</span>
            <span v-else>{{ isEdit ? 'Save Changes' : 'Set Alert' }}</span>
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active { transition: opacity 0.18s ease; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }
</style>
