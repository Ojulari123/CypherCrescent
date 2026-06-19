<script setup lang="ts">
const ui = useUiStore()
// Sync Pinia dark state with whatever the inline head script already applied.
onMounted(() => ui.initTheme())
</script>

<template>
  <div>
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
    <AppToasts />
  </div>
</template>
