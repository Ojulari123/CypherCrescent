<script setup lang="ts">
import { Trash2 } from 'lucide-vue-next'

const ui = useUiStore()
const portfolio = usePortfolioStore()
const open = computed(() => ui.deleteHoldingId != null)

async function confirm() {
  const id = ui.deleteHoldingId
  if (id == null) return
  try {
    await portfolio.deleteHolding(id)
    ui.toast('Holding removed')
  } catch {
    ui.toast('Failed to remove holding')
  }
  ui.cancelDelete()
}
</script>

<template>
  <Transition name="fade">
    <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm" @click="ui.cancelDelete()">
      <div class="w-full max-w-sm rounded-xl border border-border bg-card p-6 text-center shadow-2xl" role="alertdialog" aria-modal="true" @click.stop>
        <div class="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-red-500/10 text-red-500">
          <Trash2 class="h-5 w-5" />
        </div>
        <h3 class="text-lg font-bold">Delete holding?</h3>
        <p class="mt-1 text-sm text-muted-foreground">This removes the position from your portfolio. You can add it again later.</p>
        <div class="mt-5 grid grid-cols-2 gap-3">
          <button class="rounded-lg border border-border bg-background py-2.5 text-sm font-semibold transition-colors hover:bg-muted" @click="ui.cancelDelete()">Cancel</button>
          <button :disabled="portfolio.mutating" class="rounded-lg bg-red-500 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-60" @click="confirm">
            {{ portfolio.mutating ? 'Deleting…' : 'Delete' }}
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
