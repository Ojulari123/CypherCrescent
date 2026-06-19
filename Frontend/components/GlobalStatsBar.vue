<script setup lang="ts">
import { fmtCompact } from '~/utils/format'

// The backend has no global-market endpoint, so these are derived from the
// coins currently loaded in the Markets store (honest, not fabricated).
const market = useMarketStore()

const totalCap = computed(() => market.coins.reduce((s, c) => s + (c.market_cap ?? 0), 0))
const btc = computed(() => market.coins.find((c) => c.id === 'bitcoin'))
const eth = computed(() => market.coins.find((c) => c.id === 'ethereum'))
const btcDom = computed(() => (totalCap.value && btc.value?.market_cap ? (btc.value.market_cap / totalCap.value) * 100 : null))
const ethDom = computed(() => (totalCap.value && eth.value?.market_cap ? (eth.value.market_cap / totalCap.value) * 100 : null))

const items = computed(() => {
  const list = [
    { label: 'Coins tracked', value: String(market.coins.length) },
    { label: 'Market Cap', value: totalCap.value ? fmtCompact(totalCap.value) : '—' },
  ]
  if (btcDom.value != null) list.push({ label: 'BTC Dominance', value: `${btcDom.value.toFixed(1)}%` })
  if (ethDom.value != null) list.push({ label: 'ETH Dominance', value: `${ethDom.value.toFixed(1)}%` })
  list.push({ label: 'Powered by', value: 'CoinGecko' })
  return list
})
</script>

<template>
  <!-- Continuous ticker: the row scrolls left, exits, and loops seamlessly.
       Four identical groups + a -50% translate make the wrap invisible and keep
       the bar filled even on very wide screens. -->
  <div class="cc-ticker overflow-hidden border-b border-border bg-card">
    <div class="cc-track flex w-max">
      <div
        v-for="n in 4"
        :key="n"
        class="flex shrink-0 items-center gap-8 px-4 py-2 text-xs"
        :aria-hidden="n === 1 ? undefined : 'true'"
      >
        <span v-for="it in items" :key="it.label" class="flex items-center gap-1 whitespace-nowrap">
          <span class="text-muted-foreground">{{ it.label }}:</span><span class="font-semibold">{{ it.value }}</span>
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cc-track {
  animation: cc-scroll 30s linear infinite;
}
/* Pause when the user hovers so they can read a value. */
.cc-ticker:hover .cc-track {
  animation-play-state: paused;
}
@keyframes cc-scroll {
  from {
    transform: translateX(0);
  }
  to {
    transform: translateX(-50%);
  }
}
@media (prefers-reduced-motion: reduce) {
  .cc-track {
    animation: none;
  }
}
</style>
