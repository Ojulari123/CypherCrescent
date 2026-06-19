<script setup lang="ts">
import { Bell, Plus, Trash2, Check, Loader2, Pencil, RotateCcw } from 'lucide-vue-next'
import { fmtPrice, fmtDateTime } from '~/utils/format'
import type { PriceAlert } from '~/types/api'

const alertStore = useAlertStore()
const marketStore = useMarketStore()
const ui = useUiStore()

const showModal = ref(false)
const editingAlert = ref<PriceAlert | null>(null)
const deletingId = ref<number | null>(null)
const reactivatingId = ref<number | null>(null)

function openEdit(alert: PriceAlert) {
  editingAlert.value = alert
}

function closeModal() {
  showModal.value = false
  editingAlert.value = null
}

onMounted(async () => {
  await alertStore.load()
  const slugs = [...new Set(alertStore.items.map((a) => a.coin_slug))]
  if (slugs.length) await marketStore.ensureCoins(slugs)
})

async function deleteAlert(alert: PriceAlert) {
  deletingId.value = alert.id
  try {
    await alertStore.remove(alert.id)
    ui.toast('Alert deleted')
  } catch {
    ui.toast('Could not delete alert')
  } finally {
    deletingId.value = null
  }
}

async function reactivateAlert(alert: PriceAlert) {
  reactivatingId.value = alert.id
  try {
    await alertStore.reactivate(alert.id)
    ui.toast('Alert reactivated')
  } catch (e: any) {
    ui.toast(e?.data?.detail || 'Could not reactivate alert')
  } finally {
    reactivatingId.value = null
  }
}

function coinLabel(slug: string) {
  const c = marketStore.bySlug(slug)
  return c ? `${c.name} (${c.symbol})` : slug
}
</script>

<template>
  <div class="space-y-6">
    <!-- header -->
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 class="text-xl font-bold md:text-2xl">Price Alerts</h1>
        <p class="mt-0.5 text-sm text-muted-foreground">
          Email notifications when a coin hits your target price.
          <span class="font-medium text-foreground">{{ alertStore.activeCount }}/10</span> active alerts used.
        </p>
      </div>
      <button
        class="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-2 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 active:scale-[0.98]"
        :disabled="alertStore.activeCount >= 10"
        @click="showModal = true"
      >
        <Plus class="h-4 w-4" /> New alert
      </button>
    </div>

    <!-- loading skeleton -->
    <div v-if="alertStore.loading" class="space-y-3">
      <div v-for="i in 3" :key="i" class="h-16 animate-pulse rounded-xl bg-muted" />
    </div>

    <!-- empty state -->
    <div
      v-else-if="!alertStore.items.length"
      class="rounded-xl border border-dashed border-border py-16 text-center"
    >
      <Bell class="mx-auto mb-2 h-7 w-7 text-muted-foreground" />
      <p class="font-medium">No alerts set</p>
      <p class="mt-1 text-sm text-muted-foreground">
        Create an alert to be emailed when a coin crosses your target price.
      </p>
      <button
        class="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
        @click="showModal = true"
      >
        <Plus class="h-4 w-4" /> New alert
      </button>
    </div>

    <template v-else>
      <!-- active alerts -->
      <div v-if="alertStore.active.length" class="space-y-2">
        <h2 class="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          Active ({{ alertStore.activeCount }}/10)
        </h2>
        <div
          v-for="alert in alertStore.active"
          :key="alert.id"
          class="flex items-center gap-3 rounded-xl border border-border bg-card p-4"
        >
          <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full" :class="alert.direction === 'above' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500'">
            <span class="text-base font-bold">{{ alert.direction === 'above' ? '↑' : '↓' }}</span>
          </div>
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-semibold">{{ coinLabel(alert.coin_slug) }}</p>
            <p class="text-xs text-muted-foreground">
              {{ alert.direction === 'above' ? 'Above' : 'Below' }}
              <span class="font-semibold tabular-nums text-foreground">{{ fmtPrice(alert.target_price) }}</span>
              <template v-if="marketStore.bySlug(alert.coin_slug)?.current_price != null">
                · now {{ fmtPrice(marketStore.bySlug(alert.coin_slug)!.current_price!) }}
              </template>
            </p>
          </div>
          <div class="flex shrink-0 items-center gap-1">
            <button
              class="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              aria-label="Edit alert"
              @click="openEdit(alert)"
            >
              <Pencil class="h-4 w-4" />
            </button>
            <button
              class="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-red-500/10 hover:text-red-500 disabled:opacity-40"
              :disabled="deletingId === alert.id"
              aria-label="Delete alert"
              @click="deleteAlert(alert)"
            >
              <Loader2 v-if="deletingId === alert.id" class="h-4 w-4 animate-spin" />
              <Trash2 v-else class="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      <!-- triggered alerts -->
      <div v-if="alertStore.triggered.length" class="space-y-2">
        <h2 class="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Triggered</h2>
        <div
          v-for="alert in alertStore.triggered"
          :key="alert.id"
          class="flex items-center gap-3 rounded-xl border border-border bg-card p-4 opacity-60"
        >
          <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
            <Check class="h-4 w-4" />
          </div>
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-semibold">{{ coinLabel(alert.coin_slug) }}</p>
            <p class="text-xs text-muted-foreground">
              {{ alert.direction === 'above' ? 'Above' : 'Below' }}
              <span class="font-semibold tabular-nums text-foreground">{{ fmtPrice(alert.target_price) }}</span>
              <template v-if="alert.triggered_at">
                · triggered {{ fmtDateTime(alert.triggered_at) }}
              </template>
            </p>
          </div>
          <div class="flex shrink-0 items-center gap-1">
            <button
              class="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-primary/10 hover:text-primary disabled:opacity-40"
              :disabled="reactivatingId === alert.id || alertStore.activeCount >= 10"
              :title="alertStore.activeCount >= 10 ? '10/10 limit reached' : 'Reactivate alert'"
              aria-label="Reactivate alert"
              @click="reactivateAlert(alert)"
            >
              <Loader2 v-if="reactivatingId === alert.id" class="h-4 w-4 animate-spin" />
              <RotateCcw v-else class="h-4 w-4" />
            </button>
            <button
              class="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-red-500/10 hover:text-red-500 disabled:opacity-40"
              :disabled="deletingId === alert.id"
              aria-label="Delete alert"
              @click="deleteAlert(alert)"
            >
              <Loader2 v-if="deletingId === alert.id" class="h-4 w-4 animate-spin" />
              <Trash2 v-else class="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </template>

    <!-- create / edit modal -->
    <AlertModal v-if="showModal" @close="closeModal" />
    <AlertModal v-if="editingAlert" :alert="editingAlert" @close="closeModal" />
  </div>
</template>
