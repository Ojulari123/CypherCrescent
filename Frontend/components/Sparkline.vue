<script setup lang="ts">
const props = withDefaults(defineProps<{
  values: number[]
  color: string
  width?: number
  height?: number
}>(), { width: 120, height: 36 })

const line = computed(() => {
  const { values, width: w, height: h } = props
  const pad = 2
  if (!values.length) return ''
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const stepX = (w - pad * 2) / (values.length - 1 || 1)
  return values
    .map((v, i) => {
      const x = pad + i * stepX
      const y = pad + (1 - (v - min) / range) * (h - pad * 2)
      return `${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`
    })
    .join(' ')
})
</script>

<template>
  <svg :viewBox="`0 0 ${width} ${height}`" width="100%" :height="height" preserveAspectRatio="none" class="overflow-visible">
    <path :d="line" fill="none" :stroke="color" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
  </svg>
</template>
