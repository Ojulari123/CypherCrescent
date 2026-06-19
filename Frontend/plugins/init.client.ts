// Runs once on client boot: restore theme + hydrate the session from storage.
export default defineNuxtPlugin(async () => {
  const ui = useUiStore()
  ui.initTheme()

  const auth = useAuthStore()
  await auth.init()
})
