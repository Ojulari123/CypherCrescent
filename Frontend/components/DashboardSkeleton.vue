<!-- Loading placeholder for the dashboard. Mirrors index.vue: stat cards row,
     chart + allocation row, and the holdings table. -->
<template>
  <div class="space-y-5">
    <!-- stat cards -->
    <div class="grid grid-cols-2 gap-3 xl:grid-cols-4">
      <div v-for="i in 4" :key="i" class="rounded-xl border border-border bg-card p-5">
        <div class="flex items-center justify-between">
          <SkeletonBase class="h-3 w-24" />
          <SkeletonBase class="h-7 w-7 !rounded-full" />
        </div>
        <SkeletonBase class="mt-4 h-7 w-32" />
        <SkeletonBase class="mt-2 h-3 w-20" />
      </div>
    </div>

    <!-- chart + allocation -->
    <div class="grid grid-cols-1 gap-3 lg:grid-cols-3">
      <div class="rounded-xl border border-border bg-card p-5 lg:col-span-2">
        <SkeletonBase class="h-3 w-28" />
        <SkeletonBase class="mt-2 h-8 w-40" />
        <SkeletonBase class="mt-4 h-[250px] w-full" />
      </div>
      <div class="rounded-xl border border-border bg-card p-5">
        <SkeletonBase class="h-4 w-24" />
        <div class="mt-6 flex justify-center">
          <SkeletonBase class="h-[180px] w-[180px] !rounded-full" />
        </div>
        <div class="mt-6 space-y-2">
          <div v-for="i in 4" :key="i" class="flex items-center justify-between">
            <SkeletonBase class="h-3 w-20" />
            <SkeletonBase class="h-3 w-10" />
          </div>
        </div>
      </div>
    </div>

    <!-- holdings table -->
    <div class="rounded-xl border border-border bg-card">
      <div class="flex items-center justify-between p-5 pb-3">
        <SkeletonBase class="h-4 w-28" />
        <SkeletonBase class="h-7 w-16" />
      </div>
      <div class="space-y-3 px-5 pb-5">
        <div v-for="i in 5" :key="i" class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <SkeletonBase class="h-[30px] w-[30px] !rounded-full" />
            <div class="space-y-1.5">
              <SkeletonBase class="h-3.5 w-28" />
              <SkeletonBase class="h-2.5 w-12" />
            </div>
          </div>
          <SkeletonBase class="h-3.5 w-20" />
        </div>
      </div>
    </div>
  </div>
</template>
