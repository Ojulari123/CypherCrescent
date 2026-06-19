<script setup lang="ts">
import { Loader2, CheckCircle2, XCircle } from 'lucide-vue-next'

definePageMeta({ layout: 'auth' })
const auth = useAuthStore()
const route = useRoute()

const status = ref<'loading' | 'ok' | 'error'>('loading')
const message = ref('')

onMounted(async () => {
  const token = typeof route.query.token === 'string' ? route.query.token : ''
  if (!token) { status.value = 'error'; message.value = 'Missing verification token.'; return }
  try {
    await auth.verifyEmail(token)
    status.value = 'ok'
    message.value = 'Your email has been verified.'
  } catch (e: any) {
    status.value = 'error'
    message.value = e?.data?.detail || 'This verification link is invalid or has expired.'
  }
})
</script>

<template>
  <div class="text-center">
    <template v-if="status === 'loading'">
      <Loader2 class="mx-auto h-10 w-10 animate-spin text-primary" />
      <h2 class="mt-4 text-2xl font-bold">Verifying your email…</h2>
    </template>
    <template v-else-if="status === 'ok'">
      <div class="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-500"><CheckCircle2 class="h-7 w-7" /></div>
      <h2 class="mt-4 text-2xl font-bold">Email verified</h2>
      <p class="mt-1 text-sm text-muted-foreground">{{ message }}</p>
      <NuxtLink :to="auth.isAuthenticated ? '/' : '/login'" class="mt-6 inline-flex rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground hover:opacity-90">
        {{ auth.isAuthenticated ? 'Go to dashboard' : 'Go to sign in' }}
      </NuxtLink>
    </template>
    <template v-else>
      <div class="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-red-500/10 text-red-500"><XCircle class="h-7 w-7" /></div>
      <h2 class="mt-4 text-2xl font-bold">Verification failed</h2>
      <p class="mt-1 text-sm text-muted-foreground">{{ message }}</p>
      <NuxtLink to="/login" class="mt-6 inline-flex rounded-xl border border-border px-4 py-2.5 text-sm font-semibold hover:bg-muted">Back to sign in</NuxtLink>
    </template>
  </div>
</template>
