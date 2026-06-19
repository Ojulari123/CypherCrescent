<script setup lang="ts">
// Static aurora backdrop + a grid whose cells light up on hover. Colors are
// written straight to the hovered node (event delegation on the grid, so it's
// just two listeners regardless of cell count).
const CELL = 46
const count = ref(0)

const colors = [
  'rgba(56,189,248,0.95)', // sky-400
  'rgba(167,139,250,0.95)', // violet-400
  'rgba(34,211,238,0.90)', // cyan-400
  'rgba(96,165,250,0.95)', // blue-400
  'rgba(244,114,182,0.90)', // pink-400
]

function calc() {
  // Oversize past the viewport so the slanted grid still covers every corner.
  const cols = Math.ceil((window.innerWidth * 1.7) / CELL) + 1
  const rows = Math.ceil((window.innerHeight * 1.7) / CELL) + 1
  count.value = cols * rows
}

function paint(e: MouseEvent) {
  const t = e.target as HTMLElement
  if (!t.classList?.contains('cc-cell')) return
  t.style.transition = 'none'
  t.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)]
}
function unpaint(e: MouseEvent) {
  const t = e.target as HTMLElement
  if (!t.classList?.contains('cc-cell')) return
  t.style.transition = 'background-color 2.8s ease'
  t.style.backgroundColor = ''
}

onMounted(() => {
  calc()
  window.addEventListener('resize', calc)
})
onBeforeUnmount(() => window.removeEventListener('resize', calc))
</script>

<template>
  <div class="relative flex min-h-screen w-full items-center justify-center overflow-hidden bg-[#0a1020] px-4 py-10 text-white">
    <!-- aurora mesh: soft colored glows drifting slowly behind everything -->
    <div class="pointer-events-none absolute inset-0">
      <div class="cc-blob cc-blob-1" />
      <div class="cc-blob cc-blob-2" />
      <div class="cc-blob cc-blob-3" />
    </div>

    <!-- interactive grid: hover a cell to light it up -->
    <div class="cc-grid absolute" @mouseover="paint" @mouseout="unpaint">
      <div v-for="i in count" :key="i" class="cc-cell" />
    </div>

    <!-- vignette to deepen the corners and focus the card -->
    <div class="pointer-events-none absolute inset-0" style="background: radial-gradient(ellipse at center, transparent 40%, rgba(4,7,18,0.65) 100%)" />

    <div class="relative z-10 w-full max-w-md">
      <!-- brand -->
      <div class="mb-6 flex items-center justify-center gap-2.5">
        <svg viewBox="0 0 24 24" class="h-9 w-9" aria-hidden="true">
          <mask id="cc-auth">
            <rect width="24" height="24" fill="#000" />
            <circle cx="11" cy="12" r="8.5" fill="#fff" />
            <circle cx="15.2" cy="12" r="6.6" fill="#000" />
          </mask>
          <rect width="24" height="24" fill="#fff" mask="url(#cc-auth)" />
          <circle cx="16.4" cy="12" r="1.7" fill="#fff" />
        </svg>
        <span class="text-lg font-bold">Cypher Crescent</span>
      </div>

      <!-- form card -->
      <div class="rounded-2xl border border-white/10 bg-card/90 p-7 text-foreground shadow-2xl shadow-black/40 backdrop-blur-xl sm:p-8">
        <slot />
      </div>

      <p class="mt-5 text-center text-xs text-white/50">© 2026 Cypher Crescent · Crypto portfolio tracking</p>
    </div>
  </div>
</template>

<style scoped>
.cc-blob {
  position: absolute;
  border-radius: 9999px;
  filter: blur(80px);
  opacity: 0.55;
  will-change: transform;
}
.cc-blob-1 {
  top: -10%;
  left: -8%;
  width: 38rem;
  height: 38rem;
  background: radial-gradient(circle, #3861fb, transparent 60%);
  animation: cc-drift-1 22s ease-in-out infinite;
}
.cc-blob-2 {
  top: 25%;
  right: -12%;
  width: 36rem;
  height: 36rem;
  background: radial-gradient(circle, #7c5cff, transparent 60%);
  animation: cc-drift-2 26s ease-in-out infinite;
}
.cc-blob-3 {
  bottom: -16%;
  left: 20%;
  width: 34rem;
  height: 34rem;
  background: radial-gradient(circle, #22d3ee, transparent 62%);
  opacity: 0.4;
  animation: cc-drift-3 30s ease-in-out infinite;
}
.cc-grid {
  top: -35%;
  left: -35%;
  width: 170%;
  height: 170%;
  display: grid;
  grid-template-columns: repeat(auto-fill, 46px);
  grid-auto-rows: 46px;
  transform: rotate(-9deg) skewY(-11deg);
  transform-origin: center;
  -webkit-mask-image: radial-gradient(ellipse at center, #000 35%, transparent 72%);
  mask-image: radial-gradient(ellipse at center, #000 35%, transparent 72%);
}
.cc-cell {
  border-right: 1px solid rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  transition: background-color 2.8s ease;
}
@keyframes cc-drift-1 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(40px, 30px); }
}
@keyframes cc-drift-2 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-50px, 40px); }
}
@keyframes cc-drift-3 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(30px, -40px); }
}
@media (prefers-reduced-motion: reduce) {
  .cc-blob { animation: none; }
}
</style>
