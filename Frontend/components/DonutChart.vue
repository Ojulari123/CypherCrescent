<script setup lang="ts">
interface Slice { label: string; value: number; color: string }

const props = withDefaults(defineProps<{
  data: Slice[]
  size?: number
  active?: string | null
}>(), { size: 200, active: null })

const emit = defineEmits<{ (e: 'hover', label: string | null): void }>()

// How much the active arc thickens on hover. The radius reserves room for it
// (plus 1px) so the expanded ring never spills past the SVG viewBox and clips.
const hoverGrow = 6
const r = computed(() => props.size / 2)
const stroke = computed(() => props.size * 0.16)
const radius = computed(() => r.value - (stroke.value + hoverGrow) / 2 - 1)
const circ = computed(() => 2 * Math.PI * radius.value)
const total = computed(() => props.data.reduce((s, d) => s + d.value, 0) || 1)

const arcs = computed(() => {
  let offset = 0
  return props.data.map((d) => {
    const frac = d.value / total.value
    const dash = frac * circ.value
    const arc = { ...d, dash, offset, gap: circ.value - dash }
    offset += dash
    return arc
  })
})
</script>

<template>
  <svg :viewBox="`0 0 ${size} ${size}`" :width="size" :height="size" class="max-w-full">
    <g :transform="`rotate(-90 ${r} ${r})`">
      <circle
        v-for="d in arcs"
        :key="d.label"
        :cx="r"
        :cy="r"
        :r="radius"
        fill="none"
        :stroke="d.color"
        :stroke-width="active === d.label ? stroke + hoverGrow : stroke"
        :stroke-dasharray="`${d.dash} ${d.gap}`"
        :stroke-dashoffset="-d.offset"
        class="cursor-pointer transition-all duration-200"
        :style="{ opacity: active && active !== d.label ? 0.4 : 1 }"
        @mouseenter="emit('hover', d.label)"
        @mouseleave="emit('hover', null)"
      />
    </g>
  </svg>
</template>
