<script setup lang="ts">
import { Mail, Lock, User, Eye, EyeOff, ArrowRight, Loader2 } from 'lucide-vue-next'

definePageMeta({ layout: 'auth' })

const auth = useAuthStore()
const ui = useUiStore()
const router = useRouter()
const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const firstName = ref('')
const lastName = ref('')
const email = ref('')
const password = ref('')
const confirm = ref('')
const show = ref(false)
const submitting = ref(false)
const formError = ref('')
const errors = reactive<Record<string, string>>({})

const strength = computed(() => {
  let s = 0
  if (password.value.length >= 8) s++
  if (/[A-Z]/.test(password.value)) s++
  if (/[0-9]/.test(password.value)) s++
  if (/[^A-Za-z0-9]/.test(password.value)) s++
  return s
})
const strengthColor = (i: number) =>
  i < strength.value ? (strength.value <= 1 ? 'bg-red-500' : strength.value === 2 ? 'bg-amber-500' : 'bg-emerald-500') : 'bg-muted'

async function submit() {
  formError.value = ''
  errors.firstName = firstName.value.trim() ? '' : 'Required'
  errors.lastName = lastName.value.trim() ? '' : 'Required'
  errors.email = emailRe.test(email.value) ? '' : 'Enter a valid email'
  errors.password = password.value.length < 8 ? 'At least 8 characters' : ''
  errors.confirm = confirm.value !== password.value ? 'Passwords do not match' : ''
  if (Object.values(errors).some(Boolean)) return
  submitting.value = true
  try {
    await auth.register({
      first_name: firstName.value.trim(),
      last_name: lastName.value.trim(),
      email: email.value.trim(),
      password: password.value,
    })
    ui.toast('Account created — verification email sent')
    router.push('/')
  } catch (e: any) {
    formError.value = e?.data?.detail || 'Could not create your account'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div>
    <div class="mb-6 text-center">
      <h2 class="text-2xl font-bold">Create your account</h2>
      <p class="mt-1.5 text-sm text-muted-foreground">Start tracking your crypto in seconds.</p>
    </div>

    <div class="space-y-3">
      <div class="grid grid-cols-2 gap-3">
        <div>
          <div class="flex items-center gap-2.5 rounded-xl border bg-background px-3.5 focus-within:ring-2 focus-within:ring-primary/25" :class="errors.firstName ? 'border-red-500' : 'border-border'">
            <User class="h-4 w-4 shrink-0 text-muted-foreground" />
            <input v-model="firstName" placeholder="First name" class="w-full bg-transparent py-2.5 text-sm outline-none" />
          </div>
          <p v-if="errors.firstName" class="mt-1 text-xs text-red-500">{{ errors.firstName }}</p>
        </div>
        <div>
          <div class="flex items-center gap-2.5 rounded-xl border bg-background px-3.5 focus-within:ring-2 focus-within:ring-primary/25" :class="errors.lastName ? 'border-red-500' : 'border-border'">
            <User class="h-4 w-4 shrink-0 text-muted-foreground" />
            <input v-model="lastName" placeholder="Last name" class="w-full bg-transparent py-2.5 text-sm outline-none" />
          </div>
          <p v-if="errors.lastName" class="mt-1 text-xs text-red-500">{{ errors.lastName }}</p>
        </div>
      </div>

      <div>
        <div class="flex items-center gap-2.5 rounded-xl border bg-background px-3.5 focus-within:ring-2 focus-within:ring-primary/25" :class="errors.email ? 'border-red-500' : 'border-border'">
          <Mail class="h-4 w-4 shrink-0 text-muted-foreground" />
          <input v-model="email" type="email" placeholder="you@email.com" class="w-full bg-transparent py-2.5 text-sm outline-none" />
        </div>
        <p v-if="errors.email" class="mt-1 text-xs text-red-500">{{ errors.email }}</p>
      </div>

      <div>
        <div class="flex items-center gap-2.5 rounded-xl border bg-background px-3.5 focus-within:ring-2 focus-within:ring-primary/25" :class="errors.password ? 'border-red-500' : 'border-border'">
          <Lock class="h-4 w-4 shrink-0 text-muted-foreground" />
          <input v-model="password" :type="show ? 'text' : 'password'" placeholder="Password" class="w-full bg-transparent py-2.5 text-sm outline-none" />
          <button class="text-muted-foreground hover:text-foreground" aria-label="Toggle password" @click="show = !show">
            <EyeOff v-if="show" class="h-4 w-4" /><Eye v-else class="h-4 w-4" />
          </button>
        </div>
        <div v-if="password.length" class="mt-2 flex gap-1">
          <span v-for="i in 4" :key="i" class="h-1 flex-1 rounded-full transition-colors" :class="strengthColor(i - 1)" />
        </div>
        <p v-if="errors.password" class="mt-1 text-xs text-red-500">{{ errors.password }}</p>
      </div>

      <div>
        <div class="flex items-center gap-2.5 rounded-xl border bg-background px-3.5 focus-within:ring-2 focus-within:ring-primary/25" :class="errors.confirm ? 'border-red-500' : 'border-border'">
          <Lock class="h-4 w-4 shrink-0 text-muted-foreground" />
          <input v-model="confirm" :type="show ? 'text' : 'password'" placeholder="Confirm password" class="w-full bg-transparent py-2.5 text-sm outline-none" @keydown.enter="submit" />
        </div>
        <p v-if="errors.confirm" class="mt-1 text-xs text-red-500">{{ errors.confirm }}</p>
      </div>
    </div>

    <p v-if="formError" class="mt-3 rounded-lg bg-red-500/10 px-3 py-2 text-xs font-medium text-red-500">{{ formError }}</p>

    <button :disabled="submitting" class="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-primary py-3 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-70 active:scale-[0.99]" @click="submit">
      <Loader2 v-if="submitting" class="h-4 w-4 animate-spin" />
      <template v-else>Create account <ArrowRight class="h-4 w-4" /></template>
    </button>

    <p class="mt-5 text-center text-sm text-muted-foreground">
      Already registered?
      <NuxtLink to="/login" class="font-semibold text-primary hover:underline">Sign in</NuxtLink>
    </p>
  </div>
</template>
