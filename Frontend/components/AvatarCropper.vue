<script setup lang="ts">
import { ZoomIn, ZoomOut, Loader2 } from 'lucide-vue-next'

const props = defineProps<{ src: string; busy?: boolean }>()
const emit = defineEmits<{ (e: 'cropped', file: File): void; (e: 'cancel'): void }>()

const FRAME = 280 
const OUTPUT = 512

const imgEl = ref<HTMLImageElement | null>(null)
const natural = reactive({ w: 0, h: 0 })
const zoom = ref(1)
const offset = reactive({ x: 0, y: 0 })
const loadError = ref(false)
const ready = ref(false)

const baseScale = computed(() => (natural.w && natural.h ? Math.max(FRAME / natural.w, FRAME / natural.h) : 1))
const scale = computed(() => baseScale.value * zoom.value)
const dw = computed(() => natural.w * scale.value)
const dh = computed(() => natural.h * scale.value)

function clamp() {
  offset.x = Math.min(0, Math.max(FRAME - dw.value, offset.x))
  offset.y = Math.min(0, Math.max(FRAME - dh.value, offset.y))
}

function onImgLoad() {
  const el = imgEl.value
  if (!el) return
  natural.w = el.naturalWidth
  natural.h = el.naturalHeight
  zoom.value = 1
  // center the image in the frame
  offset.x = (FRAME - dw.value) / 2
  offset.y = (FRAME - dh.value) / 2
  ready.value = true
}

// Zoom around the frame center so the focal point stays put.
function setZoom(next: number) {
  const nz = Math.min(4, Math.max(1, next))
  const cx = (FRAME / 2 - offset.x) / scale.value
  const cy = (FRAME / 2 - offset.y) / scale.value
  zoom.value = nz
  offset.x = FRAME / 2 - cx * scale.value
  offset.y = FRAME / 2 - cy * scale.value
  clamp()
}

// Drag to pan
let dragging = false
let lastX = 0
let lastY = 0
function onPointerDown(e: PointerEvent) {
  dragging = true
  lastX = e.clientX
  lastY = e.clientY
  ;(e.target as HTMLElement).setPointerCapture?.(e.pointerId)
}
function onPointerMove(e: PointerEvent) {
  if (!dragging) return
  offset.x += e.clientX - lastX
  offset.y += e.clientY - lastY
  lastX = e.clientX
  lastY = e.clientY
  clamp()
}
function onPointerUp() {
  dragging = false
}
function onWheel(e: WheelEvent) {
  e.preventDefault()
  setZoom(zoom.value - e.deltaY * 0.0015)
}

function confirmCrop() {
  const el = imgEl.value
  if (!el) return
  const s = scale.value
  const sx = -offset.x / s
  const sy = -offset.y / s
  const side = FRAME / s
  const canvas = document.createElement('canvas')
  canvas.width = OUTPUT
  canvas.height = OUTPUT
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.drawImage(el, sx, sy, side, side, 0, 0, OUTPUT, OUTPUT)
  canvas.toBlob(
    (blob) => {
      if (blob) emit('cropped', new File([blob], 'avatar.jpg', { type: 'image/jpeg' }))
    },
    'image/jpeg',
    0.92,
  )
}
</script>

<template>
  <div class="fixed inset-0 z-50 grid place-items-center bg-black/60 p-4 backdrop-blur-sm" @click.self="emit('cancel')">
    <div class="w-full max-w-sm overflow-hidden rounded-2xl border border-border bg-card shadow-xl">
      <div class="border-b border-border px-5 py-3.5">
        <h3 class="text-sm font-bold">Position your photo</h3>
        <p class="text-xs text-muted-foreground">Drag to move · scroll or use the slider to zoom</p>
      </div>

      <div class="p-5">
        <div v-if="loadError" class="grid h-[280px] place-items-center text-center text-sm text-muted-foreground">
          Couldn't load this image. Try a JPG, PNG, or WebP.
        </div>

        <div
          v-show="!loadError"
          class="relative mx-auto select-none overflow-hidden rounded-lg bg-black/40"
          :style="{ width: FRAME + 'px', height: FRAME + 'px', touchAction: 'none', cursor: 'move' }"
          @pointerdown="onPointerDown"
          @pointermove="onPointerMove"
          @pointerup="onPointerUp"
          @pointercancel="onPointerUp"
          @wheel="onWheel"
        >
          <img
            ref="imgEl"
            :src="src"
            alt=""
            draggable="false"
            class="pointer-events-none absolute max-w-none"
            :style="{ width: dw + 'px', height: dh + 'px', left: offset.x + 'px', top: offset.y + 'px', opacity: ready ? 1 : 0 }"
            @load="onImgLoad"
            @error="loadError = true"
          />
          <!-- circular guide: dims everything outside the avatar circle -->
          <div class="pointer-events-none absolute inset-0 rounded-full" style="box-shadow: 0 0 0 9999px rgba(0,0,0,0.45); outline: 2px solid rgba(255,255,255,0.7); outline-offset: -2px;" />
        </div>

        <div v-if="!loadError" class="mt-4 flex items-center gap-3">
          <button class="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground" aria-label="Zoom out" @click="setZoom(zoom - 0.2)"><ZoomOut class="h-4 w-4" /></button>
          <input type="range" min="1" max="4" step="0.01" :value="zoom" class="h-1 flex-1 cursor-pointer accent-primary" @input="setZoom(parseFloat(($event.target as HTMLInputElement).value))" />
          <button class="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground" aria-label="Zoom in" @click="setZoom(zoom + 0.2)"><ZoomIn class="h-4 w-4" /></button>
        </div>
      </div>

      <div class="flex justify-end gap-2 border-t border-border px-5 py-3">
        <button class="rounded-lg px-3 py-2 text-sm font-semibold text-muted-foreground transition-colors hover:text-foreground" @click="emit('cancel')">Cancel</button>
        <button class="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-50" :disabled="busy || loadError || !ready" @click="confirmCrop">
          <Loader2 v-if="busy" class="h-4 w-4 animate-spin" /> Use photo
        </button>
      </div>
    </div>
  </div>
</template>
