<script setup lang="ts">
import { Search, Sun, Moon, Plus, ChevronDown, Settings, LogOut } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const ui = useUiStore()
const auth = useAuthStore()
const watchlist = useWatchlistStore()

const menuOpen = ref(false)

const nav = [
  { to: '/', label: 'Dashboard' },
  { to: '/markets', label: 'Markets' },
  { to: '/watchlist', label: 'Watchlist' },
]

function isActive(to: string) {
  return to === '/' ? route.path === '/' : route.path.startsWith(to)
}

const query = computed({
  get: () => ui.query,
  set: (v: string) => ui.setQuery(v),
})

async function logout() {
  menuOpen.value = false
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  <header class="sticky top-0 z-30 border-b border-border bg-background/90 backdrop-blur-md">
    <div class="flex items-center gap-4 px-4 py-2.5 md:px-6">
      <!-- brand -->
      <NuxtLink to="/" class="flex flex-1 items-center gap-2">
        <svg viewBox="0 0 24 24" class="h-7 w-7" aria-hidden="true">
          <mask id="cc-nav">
            <rect width="24" height="24" fill="#000" />
            <circle cx="11" cy="12" r="8.5" fill="#fff" />
            <circle cx="15.2" cy="12" r="6.6" fill="#000" />
          </mask>
          <rect width="24" height="24" fill="#3861fb" mask="url(#cc-nav)" />
          <circle cx="16.4" cy="12" r="1.7" fill="#3861fb" />
        </svg>
        <span class="hidden text-sm font-bold sm:block">Cypher Crescent</span>
      </NuxtLink>

      <!-- nav -->
      <nav class="hidden items-center gap-1 md:flex">
        <NuxtLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="rounded-lg px-3 py-2 text-sm font-semibold transition-colors"
          :class="isActive(item.to) ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted hover:text-foreground'"
        >
          {{ item.label }}
          <span v-if="item.to === '/watchlist' && watchlist.items.length" class="ml-1 rounded-full bg-primary/15 px-1.5 text-[11px] font-semibold text-primary">
            {{ watchlist.items.length }}
          </span>
        </NuxtLink>
      </nav>

      <!-- actions -->
      <div class="flex flex-1 items-center justify-end gap-2">
        <div class="relative hidden lg:block">
          <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            v-model="query"
            placeholder="Search by name or symbol"
            class="w-64 rounded-lg border border-border bg-card py-2 pl-9 pr-3 text-sm outline-none transition-all focus:w-72 focus:ring-2 focus:ring-primary/20"
          />
        </div>
        <button class="rounded-lg border border-border bg-card p-2 text-muted-foreground transition-colors hover:text-foreground" aria-label="Toggle theme" @click="ui.toggleTheme()">
          <Sun v-if="ui.dark" class="h-[18px] w-[18px]" />
          <Moon v-else class="h-[18px] w-[18px]" />
        </button>
        <button
          class="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-2 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 active:scale-[0.98]"
          @click="ui.openAddHolding()"
        >
          <Plus class="h-4 w-4" /> <span class="hidden xl:inline">Add holding</span>
        </button>

        <!-- user menu -->
        <div class="relative">
          <button class="flex items-center gap-1.5 rounded-lg p-1 transition-colors hover:bg-muted" @click="menuOpen = !menuOpen">
            <img v-if="auth.user?.profile_photo_url" :src="auth.user.profile_photo_url" alt="Profile" class="h-8 w-8 shrink-0 aspect-square rounded-full object-cover" />
            <span v-else class="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-sky-400 to-blue-600 text-xs font-bold text-white">
              {{ auth.displayName.slice(0, 1).toUpperCase() }}
            </span>
            <ChevronDown class="hidden h-4 w-4 text-muted-foreground sm:block" />
          </button>
          <template v-if="menuOpen">
            <div class="fixed inset-0 z-40" @click="menuOpen = false" />
            <div class="absolute right-0 z-50 mt-2 w-52 overflow-hidden rounded-xl border border-border bg-card p-1.5 shadow-xl">
              <div class="border-b border-border px-3 py-2">
                <p class="text-sm font-semibold">{{ auth.displayName }}</p>
                <p class="truncate text-xs text-muted-foreground">{{ auth.user?.email }}</p>
              </div>
              <NuxtLink to="/settings" class="mt-1 flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground" @click="menuOpen = false">
                <Settings class="h-4 w-4" /> Settings
              </NuxtLink>
              <button class="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium text-red-500 transition-colors hover:bg-red-500/10" @click="logout">
                <LogOut class="h-4 w-4" /> Log out
              </button>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- mobile nav + search -->
    <div class="flex items-center gap-3 border-t border-border px-4 py-2 md:hidden">
      <NuxtLink
        v-for="item in nav"
        :key="item.to"
        :to="item.to"
        class="rounded-lg px-2.5 py-1.5 text-xs font-semibold"
        :class="isActive(item.to) ? 'bg-primary/10 text-primary' : 'text-muted-foreground'"
      >
        {{ item.label }}
      </NuxtLink>
      <div class="relative ml-auto min-w-0 flex-1 sm:max-w-[220px]">
        <Search class="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
        <input v-model="query" placeholder="Search by name or symbol" class="w-full rounded-lg border border-border bg-card py-1.5 pl-8 pr-2 text-xs outline-none focus:ring-2 focus:ring-primary/20" />
      </div>
    </div>
  </header>
</template>
