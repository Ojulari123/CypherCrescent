// Protected routes: anything not in PUBLIC requires a session.
const PUBLIC = new Set([
  '/login',
  '/register',
  '/verify-email',
  '/forgot-password',
  '/reset-password',
])

export default defineNuxtRouteMiddleware(async (to) => {
  // Auth state lives in localStorage (client only); enforce on the client.
  if (import.meta.server) return

  const auth = useAuthStore()
  if (!auth.ready) await auth.init()

  const isPublic = PUBLIC.has(to.path)

  if (!auth.isAuthenticated && !isPublic) {
    return navigateTo({ path: '/login', query: to.path !== '/' ? { redirect: to.fullPath } : undefined })
  }
  if (auth.isAuthenticated && (to.path === '/login' || to.path === '/register')) {
    return navigateTo('/')
  }
})
