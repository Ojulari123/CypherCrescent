<script setup lang="ts">
withDefaults(defineProps<{
  label: string
  value: string
  accent?: string
}>(), { accent: '#3861fb' })
</script>

<template>
  <div class="rounded-xl border border-border bg-card p-4 transition-shadow hover:shadow-sm">
    <div class="mb-2 flex items-center justify-between">
      <span class="text-xs font-medium text-muted-foreground">{{ label }}</span>
      <span class="flex h-7 w-7 items-center justify-center rounded-lg" :style="{ background: accent + '1a', color: accent }">
        <slot name="icon" />
      </span>
    </div>
    <p class="truncate text-2xl font-bold tabular-nums">{{ value }}</p>
    <div v-if="$slots.sub" class="mt-1 text-xs"><slot name="sub" /></div>
  </div>
</template>
