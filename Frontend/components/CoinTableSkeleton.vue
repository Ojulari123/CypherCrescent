<!-- Loading placeholder for CoinTable, so the layout doesn't jump when data arrives. -->
<script setup lang="ts">
withDefaults(defineProps<{ rows?: number }>(), { rows: 10 })
</script>

<template>
  <div class="overflow-hidden rounded-xl border border-border bg-card">
    <div class="overflow-x-auto">
      <table class="w-full min-w-[820px] text-sm">
        <thead>
          <tr class="border-b border-border text-left text-xs text-muted-foreground">
            <th class="w-8 px-4 py-3"></th>
            <th class="px-2 py-3">#</th>
            <th class="px-3 py-3">Name</th>
            <th v-for="c in ['Price', '1h %', '24h %', '7d %', 'Market Cap']" :key="c" class="px-3 py-3 text-right">{{ c }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="i in rows" :key="i" class="border-b border-border/60 last:border-0">
            <td class="px-4 py-3"><SkeletonBase class="h-4 w-4" /></td>
            <td class="px-2 py-3"><SkeletonBase class="h-3 w-4" /></td>
            <td class="px-3 py-3">
              <div class="flex items-center gap-3">
                <SkeletonBase class="h-[30px] w-[30px] !rounded-full" />
                <div class="space-y-1.5">
                  <SkeletonBase class="h-3.5 w-24" />
                  <SkeletonBase class="h-2.5 w-10" />
                </div>
              </div>
            </td>
            <td v-for="j in 5" :key="j" class="px-3 py-3"><SkeletonBase class="ml-auto h-3.5 w-16" /></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
