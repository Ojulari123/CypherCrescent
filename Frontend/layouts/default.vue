<script setup lang="ts">
const market = useMarketStore()
const watchlist = useWatchlistStore()

// Auth is client-only, so the server can't know whether the visitor is logged in.
// Painting this shell during SSR means a logged-out user hitting a protected URL
// sees a flash of the dashboard before the client-side guard redirects them to
// /login (the "sign-in page broken until refresh" symptom). Gate the shell on a
// mounted flag: server and first hydration render agree on the neutral splash, so
// there's no hydration mismatch, and the shell only appears once the client has
// mounted — by which point the guard has already redirected anyone unauthenticated.
const mounted = ref(false)

// Bootstrap data shared across app pages (nav badge, global stats, holding modal coin list).
onMounted(() => {
  mounted.value = true
  if (!market.coins.length) market.loadMarkets()
  watchlist.load()
})
</script>

<template>
  <div class="flex min-h-screen w-full flex-col bg-background text-foreground">
    <template v-if="mounted">
      <TopNav />
      <GlobalStatsBar />
      <main class="flex-1 overflow-y-auto px-4 py-6 md:px-6">
        <div class="mx-auto w-full max-w-6xl">
          <slot />
        </div>
      </main>

      <HoldingModal />
      <ConfirmDialog />
    </template>
    <div v-else class="flex min-h-screen items-center justify-center">
      <span class="h-6 w-6 animate-spin rounded-full border-2 border-muted border-t-primary" />
    </div>
  </div>
</template>
