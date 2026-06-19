<!-- Loading placeholder for the coin detail page (coins/[id].vue): header,
     price, chart, stats on the left; position/converter rail on the right. -->
<template>
  <div class="space-y-5">
    <SkeletonBase class="h-3 w-40" />

    <div class="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_340px]">
      <!-- main -->
      <div class="space-y-5">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <SkeletonBase class="h-10 w-10 !rounded-full" />
            <SkeletonBase class="h-7 w-40" />
          </div>
          <SkeletonBase class="h-9 w-28" />
        </div>

        <SkeletonBase class="h-10 w-48" />

        <div class="rounded-xl border border-border bg-card p-5">
          <div class="mb-3 flex items-center justify-between">
            <SkeletonBase class="h-4 w-40" />
            <SkeletonBase class="h-8 w-32" />
          </div>
          <SkeletonBase class="h-[300px] w-full" />
        </div>

        <div class="rounded-xl border border-border bg-card p-5">
          <SkeletonBase class="h-5 w-40" />
          <div class="mt-3 space-y-3">
            <div v-for="i in 5" :key="i" class="flex items-center justify-between border-b border-border pb-3 last:border-0">
              <SkeletonBase class="h-3 w-28" />
              <SkeletonBase class="h-3 w-20" />
            </div>
          </div>
        </div>
      </div>

      <!-- right rail -->
      <div class="space-y-4">
        <SkeletonBase class="h-12 w-full" />
        <div class="rounded-xl border border-border bg-card p-4">
          <SkeletonBase class="h-4 w-32" />
          <div class="mt-3 space-y-2">
            <div v-for="i in 3" :key="i" class="flex items-center justify-between">
              <SkeletonBase class="h-3 w-20" />
              <SkeletonBase class="h-3 w-16" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
