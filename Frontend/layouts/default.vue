<script setup lang="ts">
const market = useMarketStore()
const watchlist = useWatchlistStore()

// Bootstrap data shared across app pages (nav badge, global stats, holding modal coin list).
onMounted(() => {
  if (!market.coins.length) market.loadMarkets()
  watchlist.load()
})
</script>

<template>
  <div class="flex min-h-screen w-full flex-col bg-background text-foreground">
    <TopNav />
    <GlobalStatsBar />
    <main class="flex-1 overflow-y-auto px-4 py-6 md:px-6">
      <div class="mx-auto w-full max-w-6xl">
        <slot />
      </div>
    </main>

    <HoldingModal />
    <ConfirmDialog />
  </div>
</template>
