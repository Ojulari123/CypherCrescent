<script setup lang="ts">
import { Lock, Eye, EyeOff, Loader2, CheckCircle2 } from 'lucide-vue-next'

definePageMeta({ layout: 'auth' })
const auth = useAuthStore()
const route = useRoute()

const token = computed(() => (typeof route.query.token === 'string' ? route.query.token : ''))
const password = ref('')
const confirm = ref('')
const show = ref(false)
const submitting = ref(false)
const done = ref(false)
const error = ref('')

async function submit() {
  error.value = ''
  if (password.value.length < 8) { error.value = 'Password must be at least 8 characters'; return }
  if (confirm.value !== password.value) { error.value = 'Passwords do not match'; return }
  if (!token.value) { error.value = 'Missing or invalid reset token'; return }
  submitting.value = true
  try {
    await auth.resetPassword(token.value, password.value)
    done.value = true
  } catch (e: any) {
    error.value = e?.data?.detail || 'Reset link is invalid or expired'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div>
    <template v-if="!done">
      <h2 class="text-2xl font-bold">Set a new password</h2>
      <p class="mt-1 text-sm text-muted-foreground">Choose a strong password you haven't used before.</p>
      <div class="mt-6 space-y-3">
        <div class="flex items-center gap-2.5 rounded-xl border border-border bg-background px-3.5 focus-within:ring-2 focus-within:ring-primary/25">
          <Lock class="h-4 w-4 shrink-0 text-muted-foreground" />
          <input v-model="password" :type="show ? 'text' : 'password'" placeholder="New password" class="w-full bg-transparent py-2.5 text-sm outline-none" />
          <button class="text-muted-foreground hover:text-foreground" aria-label="Toggle password" @click="show = !show">
            <EyeOff v-if="show" class="h-4 w-4" /><Eye v-else class="h-4 w-4" />
          </button>
        </div>
        <div class="flex items-center gap-2.5 rounded-xl border border-border bg-background px-3.5 focus-within:ring-2 focus-within:ring-primary/25">
          <Lock class="h-4 w-4 shrink-0 text-muted-foreground" />
          <input v-model="confirm" :type="show ? 'text' : 'password'" placeholder="Confirm new password" class="w-full bg-transparent py-2.5 text-sm outline-none" @keydown.enter="submit" />
        </div>
      </div>
      <p v-if="error" class="mt-2 text-xs text-red-500">{{ error }}</p>
      <button :disabled="submitting" class="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-primary py-3 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-70" @click="submit">
        <Loader2 v-if="submitting" class="h-4 w-4 animate-spin" /><template v-else>Reset password</template>
      </button>
    </template>
    <template v-else>
      <div class="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-500"><CheckCircle2 class="h-6 w-6" /></div>
      <h2 class="text-2xl font-bold">Password reset</h2>
      <p class="mt-1 text-sm text-muted-foreground">Your password has been updated. You can now sign in.</p>
      <NuxtLink to="/login" class="mt-6 inline-flex rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground hover:opacity-90">Go to sign in</NuxtLink>
    </template>
  </div>
</template>
