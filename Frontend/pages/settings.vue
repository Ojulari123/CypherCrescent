<script setup lang="ts">
import {
  User as UserIcon, Mail, Lock, ShieldCheck, ShieldOff, Camera, Trash2,
  LogOut, Loader2, Check, AlertTriangle, Clock, BadgeCheck,
} from 'lucide-vue-next'
import type { ActivityLog } from '~/types/api'
import { fmtDateTime, prettyEvent } from '~/utils/format'

const auth = useAuthStore()
const ui = useUiStore()
const router = useRouter()

// ── Profile ──
const profile = reactive({
  first_name: auth.user?.first_name ?? '',
  last_name: auth.user?.last_name ?? '',
  display_name: auth.user?.display_name ?? '',
  email: auth.user?.email ?? '',
})
const savingProfile = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const uploadingPhoto = ref(false)
const cropperSrc = ref<string | null>(null)

async function saveProfile() {
  savingProfile.value = true
  try {
    await auth.updateProfile({
      first_name: profile.first_name.trim(),
      last_name: profile.last_name.trim(),
      display_name: profile.display_name.trim() || null,
      email: profile.email.trim(),
    })
    ui.toast('Profile updated')
  } catch (e: any) {
    ui.toast(e?.data?.detail || 'Could not update profile')
  } finally {
    savingProfile.value = false
  }
}

// Pick a file → open the cropper. The actual upload happens on crop-confirm.
function onPhotoPicked(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (fileInput.value) fileInput.value.value = ''
  if (!file) return
  cropperSrc.value = URL.createObjectURL(file)
}

function closeCropper() {
  if (cropperSrc.value) URL.revokeObjectURL(cropperSrc.value)
  cropperSrc.value = null
}

async function onCropped(file: File) {
  uploadingPhoto.value = true
  try {
    await auth.uploadProfilePhoto(file)
    ui.toast('Photo updated')
    closeCropper()
  } catch (err: any) {
    ui.toast(err?.data?.detail || 'Upload failed')
  } finally {
    uploadingPhoto.value = false
  }
}

async function removePhoto() {
  try {
    await auth.deleteProfilePhoto()
    ui.toast('Photo removed')
  } catch (e: any) {
    ui.toast(e?.data?.detail || 'Could not remove photo')
  }
}

// ── Email verification ──
const resending = ref(false)
async function resendVerification() {
  if (!auth.user?.email) return
  resending.value = true
  try {
    await auth.resendVerification(auth.user.email)
    ui.toast('Verification email sent')
  } finally {
    resending.value = false
  }
}

// ── Password change (two-step) ──
const pw = reactive({ current: '', next: '', confirm: '', code: '' })
const pwStep = ref<'idle' | 'code'>('idle')
const pwBusy = ref(false)

async function startPasswordChange() {
  if (pw.next !== pw.confirm) return ui.toast('New passwords do not match')
  if (pw.next.length < 8) return ui.toast('Password must be at least 8 characters')
  pwBusy.value = true
  try {
    const res = await auth.changePassword(pw.current, pw.next)
    pwStep.value = 'code'
    ui.toast(res.message || 'Code sent to your email')
  } catch (e: any) {
    ui.toast(e?.data?.detail || 'Could not start password change')
  } finally {
    pwBusy.value = false
  }
}

async function confirmPasswordChange() {
  pwBusy.value = true
  try {
    await auth.confirmChangePassword(pw.code.trim(), pw.next)
    pwStep.value = 'idle'
    pw.current = pw.next = pw.confirm = pw.code = ''
    ui.toast('Password changed')
  } catch (e: any) {
    ui.toast(e?.data?.detail || 'Invalid or expired code')
  } finally {
    pwBusy.value = false
  }
}

// ── Two-factor (two-step) ──
const twofaPending = ref<'enable' | 'disable' | null>(null)
const twofaCode = ref('')
const twofaBusy = ref(false)

async function startTwoFactor(action: 'enable' | 'disable') {
  twofaBusy.value = true
  try {
    const res = action === 'enable' ? await auth.enableTwoFactor() : await auth.disableTwoFactor()
    twofaPending.value = action
    ui.toast(res.message || 'Code sent to your email')
  } catch (e: any) {
    ui.toast(e?.data?.detail || 'Could not send code')
  } finally {
    twofaBusy.value = false
  }
}

async function confirmTwoFactor() {
  if (!twofaPending.value) return
  twofaBusy.value = true
  try {
    if (twofaPending.value === 'enable') await auth.confirmEnableTwoFactor(twofaCode.value.trim())
    else await auth.confirmDisableTwoFactor(twofaCode.value.trim())
    ui.toast(twofaPending.value === 'enable' ? 'Two-factor enabled' : 'Two-factor disabled')
    twofaPending.value = null
    twofaCode.value = ''
  } catch (e: any) {
    ui.toast(e?.data?.detail || 'Invalid or expired code')
  } finally {
    twofaBusy.value = false
  }
}

// ── Sessions ──
const signingOutAll = ref(false)
async function signOutEverywhere() {
  signingOutAll.value = true
  await auth.logoutAll()
  router.push('/login')
}

// ── Activity log ──
const activity = ref<ActivityLog[]>([])
const activityLoading = ref(true)
onMounted(async () => {
  try {
    activity.value = await auth.fetchActivity()
  } finally {
    activityLoading.value = false
  }
})

// ── Delete account ──
const deletePassword = ref('')
const deleteConfirm = ref(false)
const deleting = ref(false)
async function deleteAccount() {
  if (!deletePassword.value) return ui.toast('Enter your password to confirm')
  deleting.value = true
  try {
    await auth.deleteAccount(deletePassword.value)
    ui.toast('Account deleted')
    router.push('/register')
  } catch (e: any) {
    ui.toast(e?.data?.detail || 'Could not delete account')
  } finally {
    deleting.value = false
  }
}

const initial = computed(() => auth.displayName.slice(0, 1).toUpperCase())
const inputClass =
  'w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none transition-all focus:ring-2 focus:ring-primary/20'
</script>

<template>
  <div class="mx-auto max-w-3xl space-y-5">
    <AvatarCropper v-if="cropperSrc" :src="cropperSrc" :busy="uploadingPhoto" @cropped="onCropped" @cancel="closeCropper" />

    <div>
      <h1 class="text-xl font-bold md:text-2xl">Settings</h1>
      <p class="text-sm text-muted-foreground">Manage your profile, security, and account.</p>
    </div>

    <!-- Profile -->
    <section class="rounded-xl border border-border bg-card p-5">
      <h2 class="mb-4 flex items-center gap-2 text-sm font-bold"><UserIcon class="h-4 w-4 text-primary" /> Profile</h2>

      <div class="mb-5 flex items-center gap-4">
        <div class="relative">
          <img v-if="auth.user?.profile_photo_url" :src="auth.user.profile_photo_url" alt="Profile photo" class="h-16 w-16 rounded-full object-cover" />
          <span v-else class="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-sky-400 to-blue-600 text-xl font-bold text-white">{{ initial }}</span>
        </div>
        <div class="flex flex-wrap gap-2">
          <input ref="fileInput" type="file" accept="image/jpeg,image/png,image/webp" class="hidden" @change="onPhotoPicked" />
          <button class="inline-flex items-center gap-1.5 rounded-lg border border-border bg-background px-3 py-2 text-sm font-semibold transition-colors hover:bg-muted disabled:opacity-50" :disabled="uploadingPhoto" @click="fileInput?.click()">
            <Loader2 v-if="uploadingPhoto" class="h-4 w-4 animate-spin" /><Camera v-else class="h-4 w-4" /> Change photo
          </button>
          <button v-if="auth.user?.profile_photo_url" class="inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-semibold text-muted-foreground transition-colors hover:text-foreground" @click="removePhoto">
            <Trash2 class="h-4 w-4" /> Remove
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <label class="block">
          <span class="mb-1 block text-xs font-medium text-muted-foreground">First name</span>
          <input v-model="profile.first_name" :class="inputClass" />
        </label>
        <label class="block">
          <span class="mb-1 block text-xs font-medium text-muted-foreground">Last name</span>
          <input v-model="profile.last_name" :class="inputClass" />
        </label>
        <label class="block">
          <span class="mb-1 block text-xs font-medium text-muted-foreground">Display name</span>
          <input v-model="profile.display_name" placeholder="Optional" :class="inputClass" />
        </label>
        <label class="block">
          <span class="mb-1 block text-xs font-medium text-muted-foreground">Email</span>
          <input v-model="profile.email" type="email" :class="inputClass" />
          <span class="mt-1 block text-[11px] text-muted-foreground">Changing your email requires re-verification.</span>
        </label>
      </div>

      <div class="mt-4 flex justify-end">
        <button class="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-50" :disabled="savingProfile" @click="saveProfile">
          <Loader2 v-if="savingProfile" class="h-4 w-4 animate-spin" /><Check v-else class="h-4 w-4" /> Save changes
        </button>
      </div>
    </section>

    <!-- Email verification -->
    <section class="rounded-xl border border-border bg-card p-5">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 class="flex items-center gap-2 text-sm font-bold"><Mail class="h-4 w-4 text-primary" /> Email verification</h2>
          <p class="mt-1 text-sm text-muted-foreground">{{ auth.user?.email }}</p>
        </div>
        <span v-if="auth.user?.email_verified" class="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-semibold text-emerald-500">
          <BadgeCheck class="h-4 w-4" /> Verified
        </span>
        <button v-else class="inline-flex items-center gap-1.5 rounded-lg border border-border bg-background px-3 py-2 text-sm font-semibold transition-colors hover:bg-muted disabled:opacity-50" :disabled="resending" @click="resendVerification">
          <Loader2 v-if="resending" class="h-4 w-4 animate-spin" /><Mail v-else class="h-4 w-4" /> Resend verification
        </button>
      </div>
    </section>

    <!-- Password -->
    <section class="rounded-xl border border-border bg-card p-5">
      <h2 class="mb-4 flex items-center gap-2 text-sm font-bold"><Lock class="h-4 w-4 text-primary" /> Password</h2>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <label class="block">
          <span class="mb-1 block text-xs font-medium text-muted-foreground">Current password</span>
          <input v-model="pw.current" type="password" autocomplete="current-password" :class="inputClass" />
        </label>
        <label class="block">
          <span class="mb-1 block text-xs font-medium text-muted-foreground">New password</span>
          <input v-model="pw.next" type="password" autocomplete="new-password" :class="inputClass" />
        </label>
        <label class="block">
          <span class="mb-1 block text-xs font-medium text-muted-foreground">Confirm new</span>
          <input v-model="pw.confirm" type="password" autocomplete="new-password" :class="inputClass" />
        </label>
      </div>

      <div v-if="pwStep === 'code'" class="mt-4 rounded-lg border border-primary/30 bg-primary/5 p-3">
        <p class="mb-2 text-sm text-muted-foreground">Enter the code we emailed you to confirm the change.</p>
        <div class="flex flex-wrap items-center gap-2">
          <input v-model="pw.code" placeholder="6-digit code" class="w-40 rounded-lg border border-border bg-background px-3 py-2 text-sm tabular-nums outline-none focus:ring-2 focus:ring-primary/20" />
          <button class="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-50" :disabled="pwBusy || !pw.code" @click="confirmPasswordChange">
            <Loader2 v-if="pwBusy" class="h-4 w-4 animate-spin" /> Confirm
          </button>
          <button class="px-2 py-2 text-sm font-semibold text-muted-foreground hover:text-foreground" @click="pwStep = 'idle'">Cancel</button>
        </div>
      </div>
      <div v-else class="mt-4 flex justify-end">
        <button class="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-50" :disabled="pwBusy || !pw.current || !pw.next" @click="startPasswordChange">
          <Loader2 v-if="pwBusy" class="h-4 w-4 animate-spin" /> Update password
        </button>
      </div>
    </section>

    <!-- Two-factor -->
    <section class="rounded-xl border border-border bg-card p-5">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 class="flex items-center gap-2 text-sm font-bold">
            <component :is="auth.user?.two_factor_enabled ? ShieldCheck : ShieldOff" class="h-4 w-4 text-primary" /> Two-factor authentication
          </h2>
          <p class="mt-1 text-sm text-muted-foreground">
            {{ auth.user?.two_factor_enabled ? 'Enabled — a code is emailed on each sign-in.' : 'Add an email code to your sign-ins for extra security.' }}
          </p>
        </div>
        <button
          v-if="!twofaPending"
          class="inline-flex items-center gap-1.5 rounded-lg border border-border bg-background px-3 py-2 text-sm font-semibold transition-colors hover:bg-muted disabled:opacity-50"
          :disabled="twofaBusy"
          @click="startTwoFactor(auth.user?.two_factor_enabled ? 'disable' : 'enable')"
        >
          <Loader2 v-if="twofaBusy" class="h-4 w-4 animate-spin" />
          {{ auth.user?.two_factor_enabled ? 'Disable' : 'Enable' }}
        </button>
      </div>

      <div v-if="twofaPending" class="mt-4 rounded-lg border border-primary/30 bg-primary/5 p-3">
        <p class="mb-2 text-sm text-muted-foreground">Enter the code we emailed you to {{ twofaPending }} two-factor authentication.</p>
        <div class="flex flex-wrap items-center gap-2">
          <input v-model="twofaCode" placeholder="6-digit code" class="w-40 rounded-lg border border-border bg-background px-3 py-2 text-sm tabular-nums outline-none focus:ring-2 focus:ring-primary/20" />
          <button class="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-50" :disabled="twofaBusy || !twofaCode" @click="confirmTwoFactor">
            <Loader2 v-if="twofaBusy" class="h-4 w-4 animate-spin" /> Confirm
          </button>
          <button class="px-2 py-2 text-sm font-semibold text-muted-foreground hover:text-foreground" @click="twofaPending = null">Cancel</button>
        </div>
      </div>
    </section>

    <!-- Sessions -->
    <section class="rounded-xl border border-border bg-card p-5">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 class="flex items-center gap-2 text-sm font-bold"><LogOut class="h-4 w-4 text-primary" /> Active sessions</h2>
          <p class="mt-1 text-sm text-muted-foreground">Sign out everywhere — invalidates all tokens on every device.</p>
        </div>
        <button class="inline-flex items-center gap-1.5 rounded-lg border border-border bg-background px-3 py-2 text-sm font-semibold transition-colors hover:bg-muted disabled:opacity-50" :disabled="signingOutAll" @click="signOutEverywhere">
          <Loader2 v-if="signingOutAll" class="h-4 w-4 animate-spin" /><LogOut v-else class="h-4 w-4" /> Sign out all devices
        </button>
      </div>
    </section>

    <!-- Activity -->
    <section class="rounded-xl border border-border bg-card p-5">
      <h2 class="mb-4 flex items-center gap-2 text-sm font-bold"><Clock class="h-4 w-4 text-primary" /> Recent activity</h2>
      <div v-if="activityLoading" class="flex items-center gap-2 py-6 text-sm text-muted-foreground"><Loader2 class="h-4 w-4 animate-spin" /> Loading…</div>
      <p v-else-if="!activity.length" class="py-6 text-center text-sm text-muted-foreground">No activity recorded yet.</p>
      <ul v-else class="divide-y divide-border">
        <li v-for="a in activity" :key="a.id" class="flex items-start justify-between gap-3 py-2.5">
          <div class="min-w-0">
            <p class="text-sm font-medium">{{ prettyEvent(a.event) }}</p>
            <p class="truncate text-xs text-muted-foreground">{{ a.ip_address || 'unknown IP' }}<span v-if="a.user_agent"> · {{ a.user_agent }}</span></p>
          </div>
          <span class="shrink-0 whitespace-nowrap text-xs text-muted-foreground">{{ fmtDateTime(a.created_at) }}</span>
        </li>
      </ul>
    </section>

    <!-- Danger zone -->
    <section class="rounded-xl border border-red-500/30 bg-red-500/5 p-5">
      <h2 class="mb-1 flex items-center gap-2 text-sm font-bold text-red-500"><AlertTriangle class="h-4 w-4" /> Danger zone</h2>
      <p class="mb-4 text-sm text-muted-foreground">Deleting your account is permanent and removes your holdings and watchlist.</p>

      <template v-if="!deleteConfirm">
        <button class="inline-flex items-center gap-1.5 rounded-lg border border-red-500/40 px-3 py-2 text-sm font-semibold text-red-500 transition-colors hover:bg-red-500/10" @click="deleteConfirm = true">
          <Trash2 class="h-4 w-4" /> Delete account
        </button>
      </template>
      <template v-else>
        <div class="flex flex-wrap items-center gap-2">
          <input v-model="deletePassword" type="password" placeholder="Enter your password" class="w-56 rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-red-500/30" />
          <button class="inline-flex items-center gap-1.5 rounded-lg bg-red-500 px-4 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-50" :disabled="deleting" @click="deleteAccount">
            <Loader2 v-if="deleting" class="h-4 w-4 animate-spin" /><Trash2 v-else class="h-4 w-4" /> Permanently delete
          </button>
          <button class="px-2 py-2 text-sm font-semibold text-muted-foreground hover:text-foreground" @click="deleteConfirm = false; deletePassword = ''">Cancel</button>
        </div>
      </template>
    </section>
  </div>
</template>
