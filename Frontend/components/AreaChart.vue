<script setup lang="ts">
const props = withDefaults(defineProps<{
  values: number[]
  color: string
  height?: number
}>(), { height: 260 })

const W = 800
// useId() is stable across SSR/client, avoiding hydration mismatches.
const gid = `grad-${useId()}`
const hover = ref<number | null>(null)

const geom = computed(() => {
  const { values, height: H } = props
  const pad = 8
  if (!values.length) return { line: '', area: '', pts: [] as [number, number][] }
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const stepX = (W - pad * 2) / (values.length - 1 || 1)
  const pts = values.map((v, i) => {
    const x = pad + i * stepX
    const y = pad + (1 - (v - min) / range) * (H - pad * 2)
    return [x, y] as [number, number]
  })
  const line = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0].toFixed(2)},${p[1].toFixed(2)}`).join(' ')
  const area = `${line} L${pts[pts.length - 1][0].toFixed(2)},${H} L${pts[0][0].toFixed(2)},${H} Z`
  return { line, area, pts }
})

const min = computed(() => (props.values.length ? Math.min(...props.values) : 0))
const max = computed(() => (props.values.length ? Math.max(...props.values) : 0))
const hoverPt = computed(() => (hover.value != null ? geom.value.pts[hover.value] : null))

function onMove(e: MouseEvent) {
  const rect = (e.currentTarget as SVGSVGElement).getBoundingClientRect()
  const ratio = (e.clientX - rect.left) / rect.width
  const idx = Math.round(ratio * (props.values.length - 1))
  hover.value = Math.max(0, Math.min(props.values.length - 1, idx))
}

function usd(n: number) {
  return n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
}
</script>

<template>
  <div class="relative w-full">
    <svg
      :viewBox="`0 0 ${W} ${height}`"
      width="100%"
      :height="height"
      preserveAspectRatio="none"
      class="cursor-crosshair overflow-visible"
      role="img"
      aria-label="Price over time"
      @mousemove="onMove"
      @mouseleave="hover = null"
    >
      <defs>
        <linearGradient :id="gid" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" :stop-color="color" stop-opacity="0.32" />
          <stop offset="100%" :stop-color="color" stop-opacity="0" />
        </linearGradient>
      </defs>
      <line v-for="g in [0.25, 0.5, 0.75]" :key="g" :x1="0" :x2="W" :y1="height * g" :y2="height * g" stroke="currentColor" stroke-opacity="0.08" stroke-width="1" />
      <path :d="geom.area" :fill="`url(#${gid})`" />
      <path :d="geom.line" fill="none" :stroke="color" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
      <g v-if="hoverPt">
        <line :x1="hoverPt[0]" :x2="hoverPt[0]" :y1="0" :y2="height" :stroke="color" stroke-opacity="0.35" stroke-width="1" />
        <circle :cx="hoverPt[0]" :cy="hoverPt[1]" r="5" :fill="color" stroke="var(--card)" stroke-width="2" />
      </g>
    </svg>
    <div
      v-if="hoverPt && hover != null"
      class="pointer-events-none absolute -translate-x-1/2 -translate-y-full rounded-lg bg-foreground px-2.5 py-1.5 text-xs font-semibold text-background shadow-lg"
      :style="{ left: `${(hover / (values.length - 1)) * 100}%`, top: `${(hoverPt[1] / height) * 100}%` }"
    >
      {{ usd(values[hover]) }}
    </div>
    <div class="mt-1 flex justify-between text-[11px] text-muted-foreground">
      <span>{{ usd(min) }}</span>
      <span>{{ usd(max) }}</span>
    </div>
  </div>
</template>
