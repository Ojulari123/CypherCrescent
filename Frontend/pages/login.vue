<script setup lang="ts">
import { Mail, Lock, Eye, EyeOff, ArrowRight, ShieldCheck, Loader2 } from 'lucide-vue-next'

definePageMeta({ layout: 'auth' })

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const stage = ref<'form' | '2fa'>('form')
const email = ref('')
const password = ref('')
const show = ref(false)
const submitting = ref(false)
const errors = reactive<Record<string, string>>({})
const formError = ref('')

const challengeToken = ref('')
const digits = ref<string[]>(['', '', '', '', '', ''])
const codeError = ref('')
const verifying = ref(false)
const digitRefs = ref<HTMLInputElement[]>([])

function redirectTarget() {
  const r = route.query.redirect
  return typeof r === 'string' ? r : '/'
}

async function submit() {
  formError.value = ''
  errors.email = !emailRe.test(email.value) ? 'Enter a valid email' : ''
  errors.password = password.value.length < 8 ? 'At least 8 characters' : ''
  if (errors.email || errors.password) return
  submitting.value = true
  try {
    const res = await auth.login(email.value, password.value)
    if ('two_factor_required' in res) {
      challengeToken.value = res.challenge_token
      stage.value = '2fa'
      nextTick(() => digitRefs.value[0]?.focus())
    } else {
      router.push(redirectTarget())
    }
  } catch (e: any) {
    formError.value = e?.data?.detail || 'Invalid email or password'
  } finally {
    submitting.value = false
  }
}

function setDigit(i: number, val: string) {
  const ch = val.replace(/\D/g, '').slice(-1)
  digits.value[i] = ch
  codeError.value = ''
  if (ch && i < 5) digitRefs.value[i + 1]?.focus()
}
function onKey(i: number, e: KeyboardEvent) {
  if (e.key === 'Backspace' && !digits.value[i] && i > 0) digitRefs.value[i - 1]?.focus()
  if (e.key === 'Enter') verify()
}
async function verify() {
  const code = digits.value.join('')
  if (code.length < 6) { codeError.value = 'Enter all 6 digits'; return }
  verifying.value = true
  try {
    await auth.verifyTwoFactor(challengeToken.value, code)
    router.push(redirectTarget())
  } catch (e: any) {
    codeError.value = e?.data?.detail || 'Invalid or expired code'
  } finally {
    verifying.value = false
  }
}
</script>

<template>
  <div v-if="stage === 'form'">
    <div class="mb-6 text-center">
      <h2 class="text-2xl font-bold">Welcome back</h2>
      <p class="mt-1.5 text-sm text-muted-foreground">Sign in to pick up where you left off.</p>
    </div>

    <div class="space-y-3">
      <div>
        <div class="flex items-center gap-2.5 rounded-xl border bg-background px-3.5 transition-colors focus-within:ring-2" :class="errors.email ? 'border-red-500 focus-within:ring-red-500/25' : 'border-border focus-within:ring-primary/25'">
          <Mail class="h-4 w-4 shrink-0 text-muted-foreground" />
          <input v-model="email" type="email" placeholder="you@email.com" class="w-full bg-transparent py-2.5 text-sm outline-none" @keydown.enter="submit" />
        </div>
        <p v-if="errors.email" class="mt-1 text-xs text-red-500">{{ errors.email }}</p>
      </div>
      <div>
        <div class="flex items-center gap-2.5 rounded-xl border bg-background px-3.5 transition-colors focus-within:ring-2" :class="errors.password ? 'border-red-500 focus-within:ring-red-500/25' : 'border-border focus-within:ring-primary/25'">
          <Lock class="h-4 w-4 shrink-0 text-muted-foreground" />
          <input v-model="password" :type="show ? 'text' : 'password'" placeholder="Password" class="w-full bg-transparent py-2.5 text-sm outline-none" @keydown.enter="submit" />
          <button class="text-muted-foreground hover:text-foreground" aria-label="Toggle password" @click="show = !show">
            <EyeOff v-if="show" class="h-4 w-4" /><Eye v-else class="h-4 w-4" />
          </button>
        </div>
        <p v-if="errors.password" class="mt-1 text-xs text-red-500">{{ errors.password }}</p>
      </div>
      <div class="flex justify-end text-sm">
        <NuxtLink to="/forgot-password" class="font-medium text-primary hover:underline">Forgot password?</NuxtLink>
      </div>
    </div>

    <p v-if="formError" class="mt-3 rounded-lg bg-red-500/10 px-3 py-2 text-xs font-medium text-red-500">{{ formError }}</p>

    <button :disabled="submitting" class="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-primary py-3 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-70 active:scale-[0.99]" @click="submit">
      <Loader2 v-if="submitting" class="h-4 w-4 animate-spin" />
      <template v-else>Sign in <ArrowRight class="h-4 w-4" /></template>
    </button>

    <p class="mt-5 text-center text-sm text-muted-foreground">
      Don't have an account?
      <NuxtLink to="/register" class="font-semibold text-primary hover:underline">Sign up</NuxtLink>
    </p>
  </div>

  <!-- 2FA stage -->
  <div v-else>
    <div class="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
      <ShieldCheck class="h-6 w-6" />
    </div>
    <h2 class="text-2xl font-bold">Two-factor authentication</h2>
    <p class="mt-1 text-sm text-muted-foreground">Enter the 6-digit code sent to <span class="font-medium text-foreground">{{ email }}</span>.</p>

    <div class="mt-6 flex justify-between gap-2">
      <input
        v-for="(d, i) in digits" :key="i" :ref="(el) => { if (el) digitRefs[i] = el as HTMLInputElement }"
        :value="d" inputmode="numeric" maxlength="1"
        class="h-12 w-full rounded-xl border bg-background text-center text-lg font-bold outline-none transition-colors focus:ring-2 focus:ring-primary/25"
        :class="codeError ? 'border-red-500' : 'border-border'"
        @input="setDigit(i, ($event.target as HTMLInputElement).value)" @keydown="onKey(i, $event)"
      />
    </div>
    <p v-if="codeError" class="mt-2 text-xs text-red-500">{{ codeError }}</p>

    <button :disabled="verifying" class="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-primary py-3 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-70" @click="verify">
      <Loader2 v-if="verifying" class="h-4 w-4 animate-spin" /><template v-else>Verify &amp; continue</template>
    </button>
    <div class="mt-4 flex items-center justify-between text-sm text-muted-foreground">
      <button class="hover:text-foreground" @click="stage = 'form'">← Back</button>
    </div>
  </div>
</template>
