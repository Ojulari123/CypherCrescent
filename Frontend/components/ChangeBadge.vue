<script setup lang="ts">
import { UP, DOWN } from '~/utils/format'

const props = withDefaults(defineProps<{
  value: number | null
  showZeroNeutral?: boolean
}>(), { showZeroNeutral: true })

const neutral = computed(() => props.value == null || (props.showZeroNeutral && Math.abs(props.value) < 0.005))
const up = computed(() => (props.value ?? 0) >= 0)
const color = computed(() => (neutral.value ? 'var(--muted-foreground)' : up.value ? UP : DOWN))
</script>

<template>
  <span class="inline-flex items-center gap-1 font-medium tabular-nums" :style="{ color }">
    <span v-if="!neutral" :style="{ fontSize: '0.62em', lineHeight: 1 }">{{ up ? '▲' : '▼' }}</span>
    <template v-if="value == null">—</template>
    <template v-else>{{ Math.abs(value).toFixed(2) }}%</template>
  </span>
</template>
