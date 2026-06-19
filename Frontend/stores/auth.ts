import { defineStore } from 'pinia'
import type { User, TokenResponse, LoginResult, ActivityLog } from '~/types/api'

const ACCESS_KEY = 'cc_access'
const REFRESH_KEY = 'cc_refresh'

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  user: User | null
  ready: boolean
  _refreshing: Promise<void> | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    accessToken: null,
    refreshToken: null,
    user: null,
    ready: false,
    _refreshing: null,
  }),

  getters: {
    isAuthenticated: (s): boolean => !!s.accessToken,
    displayName: (s): string =>
      s.user?.display_name || s.user?.first_name || s.user?.email?.split('@')[0] || 'Trader',
  },

  actions: {
    apiBase(): string {
      return useRuntimeConfig().public.apiBase as string
    },

    // Load persisted tokens (client only) and hydrate the user.
    async init() {
      if (this.ready) return
      if (import.meta.client) {
        this.accessToken = localStorage.getItem(ACCESS_KEY)
        this.refreshToken = localStorage.getItem(REFRESH_KEY)
        if (this.accessToken) {
          try {
            await this.fetchMe()
          } catch {
            this.clear()
          }
        }
      }
      this.ready = true
    },

    persist() {
      if (!import.meta.client) return
      if (this.accessToken) localStorage.setItem(ACCESS_KEY, this.accessToken)
      else localStorage.removeItem(ACCESS_KEY)
      if (this.refreshToken) localStorage.setItem(REFRESH_KEY, this.refreshToken)
      else localStorage.removeItem(REFRESH_KEY)
    },

    setSession(t: TokenResponse) {
      this.accessToken = t.access_token
      this.refreshToken = t.refresh_token
      this.user = t.user
      this.persist()
    },

    clear() {
      this.accessToken = null
      this.refreshToken = null
      this.user = null
      this.persist()
    },

    // ── Public auth flows ──
    async register(payload: {
      email: string
      password: string
      first_name: string
      last_name: string
      display_name?: string
    }): Promise<void> {
      const t = await $fetch<TokenResponse>('/api/users/register', {
        baseURL: this.apiBase(),
        method: 'POST',
        body: payload,
      })
      this.setSession(t)
    },

    async login(email: string, password: string): Promise<LoginResult> {
      const res = await $fetch<LoginResult>('/api/users/login', {
        baseURL: this.apiBase(),
        method: 'POST',
        body: { email, password },
      })
      if ('access_token' in res) this.setSession(res)
      return res
    },

    async verifyTwoFactor(challengeToken: string, code: string): Promise<void> {
      const t = await $fetch<TokenResponse>('/api/users/2fa/verify', {
        baseURL: this.apiBase(),
        method: 'POST',
        body: { challenge_token: challengeToken, code },
      })
      this.setSession(t)
    },

    async fetchMe(): Promise<void> {
      this.user = await this.authFetch<User>('/api/users/me')
    },

    async logout(): Promise<void> {
      try {
        await this.authFetch('/api/users/logout', { method: 'POST' })
      } catch {
        // best-effort; clear locally regardless
      }
      this.clear()
    },

    // ── Token refresh (single-flight) ──
    async doRefresh(): Promise<void> {
      if (!this.refreshToken) throw new Error('No refresh token')
      const res = await $fetch<{ access_token: string; refresh_token: string }>(
        '/api/users/refresh',
        { baseURL: this.apiBase(), method: 'POST', body: { refresh_token: this.refreshToken } },
      )
      this.accessToken = res.access_token
      this.refreshToken = res.refresh_token
      this.persist()
    },

    // Authenticated request with automatic 401 → refresh → retry once.
    async authFetch<T>(path: string, opts: Record<string, any> = {}): Promise<T> {
      const headers = { ...(opts.headers || {}) }
      if (this.accessToken) headers.Authorization = `Bearer ${this.accessToken}`
      try {
        return await $fetch<T>(path, { baseURL: this.apiBase(), ...opts, headers })
      } catch (err: any) {
        if (err?.response?.status !== 401 || !this.refreshToken) throw err
        // refresh once (shared across concurrent calls), then retry
        if (!this._refreshing) {
          this._refreshing = this.doRefresh().finally(() => { this._refreshing = null })
        }
        try {
          await this._refreshing
        } catch {
          this.clear()
          throw err
        }
        const retryHeaders = { ...(opts.headers || {}), Authorization: `Bearer ${this.accessToken}` }
        return await $fetch<T>(path, { baseURL: this.apiBase(), ...opts, headers: retryHeaders })
      }
    },

    // Other public (no-auth) flows used by auth pages.
    async resendVerification(email: string) {
      return $fetch('/api/users/resend-verification', { baseURL: this.apiBase(), method: 'POST', body: { email } })
    },
    async forgotPassword(email: string) {
      return $fetch('/api/users/forgot-password', { baseURL: this.apiBase(), method: 'POST', body: { email } })
    },
    async resetPassword(token: string, new_password: string) {
      return $fetch('/api/users/reset-password', { baseURL: this.apiBase(), method: 'POST', body: { token, new_password } })
    },
    async verifyEmail(token: string): Promise<void> {
      const t = await $fetch<TokenResponse>('/api/users/verify-email', {
        baseURL: this.apiBase(), method: 'GET', query: { token },
      })
      if (t && 'access_token' in t) this.setSession(t)
    },

    // ── Account / settings flows (authenticated) ──

    // PATCH /api/users/me — update profile fields (changing email re-triggers verification server-side).
    async updateProfile(payload: { first_name?: string; last_name?: string; display_name?: string | null; email?: string }): Promise<void> {
      this.user = await this.authFetch<User>('/api/users/me', { method: 'PATCH', body: payload })
    },

    // PUT /api/users/me/password — step 1: validate + email a confirmation code.
    async changePassword(current_password: string, new_password: string) {
      return this.authFetch<{ two_factor_required: boolean; message: string }>('/api/users/me/password', {
        method: 'PUT',
        body: { current_password, new_password },
      })
    },
    // PUT /api/users/me/password/verify — step 2: confirm with the code (returns a fresh token pair).
    async confirmChangePassword(code: string, new_password: string): Promise<void> {
      const t = await this.authFetch<TokenResponse>('/api/users/me/password/verify', {
        method: 'PUT',
        body: { code, new_password },
      })
      this.setSession(t)
    },

    // POST /api/users/me/profile-photo (multipart) — upload, then mirror the URL onto the cached user.
    async uploadProfilePhoto(file: File): Promise<void> {
      const form = new FormData()
      form.append('file', file)
      const res = await this.authFetch<{ profile_photo_url: string }>('/api/users/me/profile-photo', { method: 'POST', body: form })
      if (this.user) this.user.profile_photo_url = res.profile_photo_url
    },
    async deleteProfilePhoto(): Promise<void> {
      await this.authFetch('/api/users/me/profile-photo', { method: 'DELETE' })
      if (this.user) this.user.profile_photo_url = null
    },

    // Two-factor: each toggle is a two-step (request code → confirm code) flow.
    async enableTwoFactor() {
      return this.authFetch<{ message: string }>('/api/users/2fa/enable', { method: 'POST' })
    },
    async confirmEnableTwoFactor(code: string): Promise<void> {
      await this.authFetch('/api/users/2fa/enable/confirm', { method: 'POST', body: { code } })
      if (this.user) this.user.two_factor_enabled = true
    },
    async disableTwoFactor() {
      return this.authFetch<{ message: string }>('/api/users/2fa/disable', { method: 'POST' })
    },
    async confirmDisableTwoFactor(code: string): Promise<void> {
      await this.authFetch('/api/users/2fa/disable/confirm', { method: 'POST', body: { code } })
      if (this.user) this.user.two_factor_enabled = false
    },

    // GET /api/users/activity — recent account events (logins, password changes, etc.).
    async fetchActivity(): Promise<ActivityLog[]> {
      return this.authFetch<ActivityLog[]>('/api/users/activity')
    },

    // POST /api/users/logout-all — invalidates every issued token, so we drop the local session too.
    async logoutAll(): Promise<void> {
      try {
        await this.authFetch('/api/users/logout-all', { method: 'POST' })
      } catch {
        // best-effort; clear locally regardless
      }
      this.clear()
    },

    // DELETE /api/users/me — permanent; requires the current password.
    async deleteAccount(password: string): Promise<void> {
      await this.authFetch('/api/users/me', { method: 'DELETE', body: { password } })
      this.clear()
    },
  },
})
