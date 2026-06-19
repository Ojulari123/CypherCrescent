<script setup lang="ts">
import { coinColor } from '~/utils/coins'

const props = withDefaults(defineProps<{
  slug: string
  symbol?: string | null
  image?: string | null
  size?: number
}>(), { size: 32 })

const errored = ref(false)
const color = computed(() => coinColor(props.slug))
const letters = computed(() => (props.symbol || props.slug || '?').slice(0, 3).toUpperCase())
const showImage = computed(() => !!props.image && !errored.value)
</script>

<template>
  <img
    v-if="showImage"
    :src="image as string"
    :alt="symbol || slug"
    :width="size"
    :height="size"
    class="shrink-0 rounded-full object-cover"
    :style="{ width: size + 'px', height: size + 'px' }"
    @error="errored = true"
  />
  <div
    v-else
    class="flex shrink-0 items-center justify-center rounded-full font-bold text-white"
    :style="{ width: size + 'px', height: size + 'px', background: color, fontSize: size * 0.34 + 'px' }"
    aria-hidden="true"
  >
    {{ letters }}
  </div>
</template>
