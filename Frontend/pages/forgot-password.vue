<script setup lang="ts">
import { Mail, ArrowLeft, Loader2, CheckCircle2 } from 'lucide-vue-next'

definePageMeta({ layout: 'auth' })
const auth = useAuthStore()

const email = ref('')
const sent = ref(false)
const submitting = ref(false)
const error = ref('')

async function submit() {
  error.value = ''
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) { error.value = 'Enter a valid email'; return }
  submitting.value = true
  try {
    await auth.forgotPassword(email.value.trim())
    sent.value = true
  } catch (e: any) {
    error.value = e?.data?.detail || 'Something went wrong'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div>
    <template v-if="!sent">
      <h2 class="text-2xl font-bold">Reset your password</h2>
      <p class="mt-1 text-sm text-muted-foreground">Enter your email and we'll send a reset link.</p>
      <div class="mt-6 flex items-center gap-2.5 rounded-xl border bg-background px-3.5 focus-within:ring-2 focus-within:ring-primary/25" :class="error ? 'border-red-500' : 'border-border'">
        <Mail class="h-4 w-4 shrink-0 text-muted-foreground" />
        <input v-model="email" type="email" placeholder="you@email.com" class="w-full bg-transparent py-2.5 text-sm outline-none" @keydown.enter="submit" />
      </div>
      <p v-if="error" class="mt-1 text-xs text-red-500">{{ error }}</p>
      <button :disabled="submitting" class="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-primary py-3 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-70" @click="submit">
        <Loader2 v-if="submitting" class="h-4 w-4 animate-spin" /><template v-else>Send reset link</template>
      </button>
    </template>
    <template v-else>
      <div class="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-500"><CheckCircle2 class="h-6 w-6" /></div>
      <h2 class="text-2xl font-bold">Check your email</h2>
      <p class="mt-1 text-sm text-muted-foreground">If an account exists for <span class="font-medium text-foreground">{{ email }}</span>, a reset link is on its way.</p>
    </template>
    <NuxtLink to="/login" class="mt-6 inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground hover:text-foreground">
      <ArrowLeft class="h-4 w-4" /> Back to sign in
    </NuxtLink>
  </div>
</template>
