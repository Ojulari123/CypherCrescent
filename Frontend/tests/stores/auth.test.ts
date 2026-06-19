import { describe, it, expect, vi } from 'vitest'
import { useAuthStore } from '~/stores/auth'

const ACCESS_KEY = 'cc_access'
const REFRESH_KEY = 'cc_refresh'

const MOCK_TOKEN = {
  access_token: 'acc-tok',
  refresh_token: 'ref-tok',
  token_type: 'bearer',
  user: {
    id: 1,
    email: 'alice@example.com',
    first_name: 'Alice',
    last_name: 'Smith',
    display_name: 'alice',
    email_verified: true,
    two_factor_enabled: false,
    profile_photo_url: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
}

const fetch = $fetch as any

// ── Initial state ─────────────────────────────────────────────────────────────

describe('initial state', () => {
  it('starts unauthenticated', () => {
    const auth = useAuthStore()
    expect(auth.accessToken).toBeNull()
    expect(auth.refreshToken).toBeNull()
    expect(auth.user).toBeNull()
    expect(auth.ready).toBe(false)
    expect(auth.isAuthenticated).toBe(false)
  })
})

// ── Getters ───────────────────────────────────────────────────────────────────

describe('displayName getter', () => {
  it('returns display_name when set', () => {
    const auth = useAuthStore()
    auth.user = { ...MOCK_TOKEN.user, display_name: 'Ace' }
    expect(auth.displayName).toBe('Ace')
  })

  it('falls back to first_name when display_name is null', () => {
    const auth = useAuthStore()
    auth.user = { ...MOCK_TOKEN.user, display_name: null }
    expect(auth.displayName).toBe('Alice')
  })

  it('falls back to email prefix when no names', () => {
    const auth = useAuthStore()
    auth.user = { ...MOCK_TOKEN.user, display_name: null, first_name: '' }
    expect(auth.displayName).toBe('alice')
  })

  it('falls back to "Trader" with no user', () => {
    const auth = useAuthStore()
    expect(auth.displayName).toBe('Trader')
  })
})

// ── setSession / clear ────────────────────────────────────────────────────────

describe('setSession', () => {
  it('stores tokens and user in state', () => {
    const auth = useAuthStore()
    auth.setSession(MOCK_TOKEN)
    expect(auth.accessToken).toBe('acc-tok')
    expect(auth.refreshToken).toBe('ref-tok')
    expect(auth.user?.email).toBe('alice@example.com')
    expect(auth.isAuthenticated).toBe(true)
  })

  it('persists tokens to localStorage', () => {
    const auth = useAuthStore()
    auth.setSession(MOCK_TOKEN)
    expect(localStorage.getItem(ACCESS_KEY)).toBe('acc-tok')
    expect(localStorage.getItem(REFRESH_KEY)).toBe('ref-tok')
  })
})

describe('clear', () => {
  it('removes tokens from state and localStorage', () => {
    const auth = useAuthStore()
    auth.setSession(MOCK_TOKEN)
    auth.clear()
    expect(auth.accessToken).toBeNull()
    expect(auth.refreshToken).toBeNull()
    expect(auth.user).toBeNull()
    expect(localStorage.getItem(ACCESS_KEY)).toBeNull()
    expect(localStorage.getItem(REFRESH_KEY)).toBeNull()
  })
})

// ── init ──────────────────────────────────────────────────────────────────────

describe('init', () => {
  it('reads tokens from localStorage and hydrates user', async () => {
    localStorage.setItem(ACCESS_KEY, 'stored-access')
    localStorage.setItem(REFRESH_KEY, 'stored-refresh')
    fetch.mockResolvedValueOnce(MOCK_TOKEN.user)

    const auth = useAuthStore()
    await auth.init()

    expect(auth.accessToken).toBe('stored-access')
    expect(auth.user?.email).toBe('alice@example.com')
    expect(auth.ready).toBe(true)
  })

  it('clears tokens if fetchMe fails', async () => {
    localStorage.setItem(ACCESS_KEY, 'bad-token')
    fetch.mockRejectedValueOnce(new Error('401'))

    const auth = useAuthStore()
    await auth.init()

    expect(auth.accessToken).toBeNull()
    expect(auth.ready).toBe(true)
  })

  it('is a no-op on second call', async () => {
    const auth = useAuthStore()
    auth.ready = true
    await auth.init()
    expect(fetch).not.toHaveBeenCalled()
  })
})

// ── login ─────────────────────────────────────────────────────────────────────

describe('login', () => {
  it('sets session on successful login', async () => {
    fetch.mockResolvedValueOnce(MOCK_TOKEN)
    const auth = useAuthStore()
    const result = await auth.login('alice@example.com', 'Secret123!')
    expect(auth.accessToken).toBe('acc-tok')
    expect(result).toEqual(MOCK_TOKEN)
  })

  it('returns 2fa challenge without setting session', async () => {
    const challenge = { two_factor_required: true, challenge_token: 'ch-tok' }
    fetch.mockResolvedValueOnce(challenge)
    const auth = useAuthStore()
    const result = await auth.login('alice@example.com', 'Secret123!')
    expect(auth.accessToken).toBeNull()
    expect(result).toEqual(challenge)
  })
})

// ── register ──────────────────────────────────────────────────────────────────

describe('register', () => {
  it('calls register endpoint and sets session', async () => {
    fetch.mockResolvedValueOnce(MOCK_TOKEN)
    const auth = useAuthStore()
    await auth.register({ email: 'alice@example.com', password: 'Secret123!', first_name: 'Alice', last_name: 'Smith' })
    expect(auth.accessToken).toBe('acc-tok')
    expect(fetch).toHaveBeenCalledWith('/api/users/register', expect.objectContaining({ method: 'POST' }))
  })
})

// ── logout ────────────────────────────────────────────────────────────────────

describe('logout', () => {
  it('calls logout endpoint and clears session', async () => {
    const auth = useAuthStore()
    auth.setSession(MOCK_TOKEN)
    fetch.mockResolvedValueOnce({})
    await auth.logout()
    expect(auth.accessToken).toBeNull()
  })

  it('clears session even if logout endpoint fails', async () => {
    const auth = useAuthStore()
    auth.setSession(MOCK_TOKEN)
    fetch.mockRejectedValueOnce(new Error('network error'))
    await auth.logout()
    expect(auth.accessToken).toBeNull()
  })
})

// ── authFetch ─────────────────────────────────────────────────────────────────

describe('authFetch', () => {
  it('attaches Authorization header when token is set', async () => {
    const auth = useAuthStore()
    auth.accessToken = 'my-token'
    fetch.mockResolvedValueOnce({ data: 'ok' })

    await auth.authFetch('/api/some-endpoint')

    expect(fetch).toHaveBeenCalledWith('/api/some-endpoint', expect.objectContaining({
      headers: expect.objectContaining({ Authorization: 'Bearer my-token' }),
    }))
  })

  it('refreshes token on 401 and retries', async () => {
    const auth = useAuthStore()
    auth.accessToken = 'old-token'
    auth.refreshToken = 'ref-tok'

    const err401 = Object.assign(new Error('401'), { response: { status: 401 } })
    fetch
      .mockRejectedValueOnce(err401)                                    // original request fails
      .mockResolvedValueOnce({ access_token: 'new-acc', refresh_token: 'new-ref' }) // refresh
      .mockResolvedValueOnce({ data: 'retried' })                       // retry

    const result = await auth.authFetch<{ data: string }>('/api/protected')
    expect(result).toEqual({ data: 'retried' })
    expect(auth.accessToken).toBe('new-acc')
  })

  it('clears session and rethrows when refresh fails', async () => {
    const auth = useAuthStore()
    auth.accessToken = 'old-token'
    auth.refreshToken = 'ref-tok'

    const err401 = Object.assign(new Error('401'), { response: { status: 401 } })
    fetch
      .mockRejectedValueOnce(err401)
      .mockRejectedValueOnce(new Error('refresh failed'))

    await expect(auth.authFetch('/api/protected')).rejects.toThrow()
    expect(auth.accessToken).toBeNull()
  })
})

// ── verifyTwoFactor ───────────────────────────────────────────────────────────

describe('verifyTwoFactor', () => {
  it('calls 2fa verify and sets session', async () => {
    fetch.mockResolvedValueOnce(MOCK_TOKEN)
    const auth = useAuthStore()
    await auth.verifyTwoFactor('ch-tok', '123456')
    expect(auth.accessToken).toBe('acc-tok')
    expect(fetch).toHaveBeenCalledWith('/api/users/2fa/verify', expect.objectContaining({ method: 'POST' }))
  })
})
