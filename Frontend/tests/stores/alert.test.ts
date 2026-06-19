import { describe, it, expect, vi } from 'vitest'
import { useAuthStore } from '~/stores/auth'
import { useAlertStore } from '~/stores/alert'

const RAW_ACTIVE = {
  id: 1,
  coin_slug: 'bitcoin',
  target_price: '65000.0',
  direction: 'above',
  triggered: false,
  triggered_at: null,
  created_at: '2026-06-01T00:00:00Z',
}

const RAW_TRIGGERED = {
  id: 2,
  coin_slug: 'ethereum',
  target_price: '3000.0',
  direction: 'below',
  triggered: true,
  triggered_at: '2026-06-15T12:00:00Z',
  created_at: '2026-06-01T00:00:00Z',
}

function setupAuth() {
  const auth = useAuthStore()
  auth.accessToken = 'test-token'
  return auth
}

// ── Initial state ─────────────────────────────────────────────────────────────

describe('initial state', () => {
  it('starts empty and not loading', () => {
    const store = useAlertStore()
    expect(store.items).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.creating).toBe(false)
    expect(store.activeCount).toBe(0)
  })
})

// ── Getters ───────────────────────────────────────────────────────────────────

describe('getters', () => {
  it('active filters to untriggered alerts', () => {
    const store = useAlertStore()
    store.items = [
      { id: 1, coin_slug: 'bitcoin', target_price: 65000, direction: 'above', triggered: false, triggered_at: null, created_at: '' },
      { id: 2, coin_slug: 'ethereum', target_price: 3000, direction: 'below', triggered: true, triggered_at: '2026-06-15T00:00:00Z', created_at: '' },
    ]
    expect(store.active).toHaveLength(1)
    expect(store.active[0].id).toBe(1)
  })

  it('triggered filters to triggered alerts', () => {
    const store = useAlertStore()
    store.items = [
      { id: 1, coin_slug: 'bitcoin', target_price: 65000, direction: 'above', triggered: false, triggered_at: null, created_at: '' },
      { id: 2, coin_slug: 'ethereum', target_price: 3000, direction: 'below', triggered: true, triggered_at: '2026-06-15T00:00:00Z', created_at: '' },
    ]
    expect(store.triggered).toHaveLength(1)
    expect(store.triggered[0].id).toBe(2)
  })

  it('activeCount counts only untriggered', () => {
    const store = useAlertStore()
    store.items = [
      { id: 1, coin_slug: 'bitcoin', target_price: 65000, direction: 'above', triggered: false, triggered_at: null, created_at: '' },
      { id: 2, coin_slug: 'bitcoin', target_price: 50000, direction: 'below', triggered: false, triggered_at: null, created_at: '' },
      { id: 3, coin_slug: 'ethereum', target_price: 3000, direction: 'below', triggered: true, triggered_at: '2026-06-15T00:00:00Z', created_at: '' },
    ]
    expect(store.activeCount).toBe(2)
  })

  it('hasActiveAlertFor returns true for untriggered slug', () => {
    const store = useAlertStore()
    store.items = [
      { id: 1, coin_slug: 'bitcoin', target_price: 65000, direction: 'above', triggered: false, triggered_at: null, created_at: '' },
    ]
    expect(store.hasActiveAlertFor('bitcoin')).toBe(true)
    expect(store.hasActiveAlertFor('ethereum')).toBe(false)
  })

  it('hasActiveAlertFor returns false for triggered slug', () => {
    const store = useAlertStore()
    store.items = [
      { id: 1, coin_slug: 'bitcoin', target_price: 65000, direction: 'above', triggered: true, triggered_at: '2026-06-15T00:00:00Z', created_at: '' },
    ]
    expect(store.hasActiveAlertFor('bitcoin')).toBe(false)
  })

  it('activeAlertsFor returns only untriggered alerts for slug', () => {
    const store = useAlertStore()
    store.items = [
      { id: 1, coin_slug: 'bitcoin', target_price: 70000, direction: 'above', triggered: false, triggered_at: null, created_at: '' },
      { id: 2, coin_slug: 'bitcoin', target_price: 60000, direction: 'above', triggered: true, triggered_at: '2026-06-15T00:00:00Z', created_at: '' },
      { id: 3, coin_slug: 'ethereum', target_price: 3000, direction: 'below', triggered: false, triggered_at: null, created_at: '' },
    ]
    const result = store.activeAlertsFor('bitcoin')
    expect(result).toHaveLength(1)
    expect(result[0].id).toBe(1)
  })
})

// ── load ──────────────────────────────────────────────────────────────────────

describe('load', () => {
  it('fetches and maps alerts (coerces string numbers)', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockResolvedValue([RAW_ACTIVE, RAW_TRIGGERED])

    const store = useAlertStore()
    await store.load()

    expect(store.items).toHaveLength(2)
    expect(store.items[0].target_price).toBe(65000)   // string → number
    expect(store.items[0].direction).toBe('above')
    expect(store.items[0].triggered).toBe(false)
    expect(store.items[1].target_price).toBe(3000)
    expect(store.items[1].triggered).toBe(true)
    expect(store.loading).toBe(false)
    expect(auth.authFetch).toHaveBeenCalledWith('/api/alerts')
  })

  it('clears loading flag on failure', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockRejectedValue(new Error('network'))

    const store = useAlertStore()
    await expect(store.load()).rejects.toThrow()
    expect(store.loading).toBe(false)
  })
})

// ── create ────────────────────────────────────────────────────────────────────

describe('create', () => {
  it('posts alert and prepends to items list', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockResolvedValue(RAW_ACTIVE)

    const store = useAlertStore()
    await store.create('bitcoin', 65000, 'above')

    expect(store.items).toHaveLength(1)
    expect(store.items[0].coin_slug).toBe('bitcoin')
    expect(store.items[0].target_price).toBe(65000)
    expect(store.creating).toBe(false)
    expect(auth.authFetch).toHaveBeenCalledWith('/api/alerts', expect.objectContaining({
      method: 'POST',
      body: { coin_slug: 'bitcoin', target_price: 65000, direction: 'above' },
    }))
  })

  it('prepends new alert before existing ones', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockResolvedValue({ ...RAW_TRIGGERED, id: 99 })

    const store = useAlertStore()
    store.items = [{ id: 1, coin_slug: 'bitcoin', target_price: 65000, direction: 'above', triggered: false, triggered_at: null, created_at: '' }]
    await store.create('ethereum', 3000, 'below')

    expect(store.items[0].id).toBe(99)   // new one first
    expect(store.items[1].id).toBe(1)
  })

  it('clears creating flag on failure', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockRejectedValue({ data: { detail: 'Limit reached' } })

    const store = useAlertStore()
    await expect(store.create('bitcoin', 65000, 'above')).rejects.toBeDefined()
    expect(store.creating).toBe(false)
    expect(store.items).toHaveLength(0)  // not added on failure
  })
})

// ── update ────────────────────────────────────────────────────────────────────

describe('update', () => {
  it('patches alert and updates item in list', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockResolvedValue({ ...RAW_ACTIVE, target_price: '75000.0', direction: 'below' })

    const store = useAlertStore()
    store.items = [{ id: 1, coin_slug: 'bitcoin', target_price: 65000, direction: 'above', triggered: false, triggered_at: null, created_at: '' }]

    await store.update(1, 75000, 'below')

    expect(store.items[0].target_price).toBe(75000)
    expect(store.items[0].direction).toBe('below')
    expect(auth.authFetch).toHaveBeenCalledWith('/api/alerts/1', expect.objectContaining({
      method: 'PATCH',
      body: { target_price: 75000, direction: 'below' },
    }))
  })

  it('leaves other items untouched', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockResolvedValue({ ...RAW_ACTIVE, id: 2, target_price: '75000.0' })

    const store = useAlertStore()
    store.items = [
      { id: 1, coin_slug: 'bitcoin', target_price: 60000, direction: 'above', triggered: false, triggered_at: null, created_at: '' },
      { id: 2, coin_slug: 'bitcoin', target_price: 65000, direction: 'above', triggered: false, triggered_at: null, created_at: '' },
    ]

    await store.update(2, 75000, 'above')

    expect(store.items[0].target_price).toBe(60000)  // item 1 unchanged
    expect(store.items[1].target_price).toBe(75000)  // item 2 updated
  })

  it('rethrows on API failure', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockRejectedValue({ data: { detail: 'Cannot edit triggered alert' } })

    const store = useAlertStore()
    store.items = [{ id: 1, coin_slug: 'bitcoin', target_price: 65000, direction: 'above', triggered: false, triggered_at: null, created_at: '' }]

    await expect(store.update(1, 75000, 'above')).rejects.toBeDefined()
    expect(store.items[0].target_price).toBe(65000)  // unchanged on failure
  })
})

// ── reactivate ────────────────────────────────────────────────────────────────

describe('reactivate', () => {
  it('posts to reactivate endpoint and updates item in list', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockResolvedValue({ ...RAW_TRIGGERED, triggered: false, triggered_at: null })

    const store = useAlertStore()
    store.items = [{ id: 2, coin_slug: 'ethereum', target_price: 3000, direction: 'below', triggered: true, triggered_at: '2026-06-15T12:00:00Z', created_at: '' }]

    await store.reactivate(2)

    expect(store.items[0].triggered).toBe(false)
    expect(store.items[0].triggered_at).toBeNull()
    expect(auth.authFetch).toHaveBeenCalledWith('/api/alerts/2/reactivate', expect.objectContaining({ method: 'POST' }))
  })

  it('leaves other items untouched', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockResolvedValue({ ...RAW_TRIGGERED, id: 2, triggered: false, triggered_at: null })

    const store = useAlertStore()
    store.items = [
      { id: 1, coin_slug: 'bitcoin', target_price: 65000, direction: 'above', triggered: true, triggered_at: '2026-06-15T12:00:00Z', created_at: '' },
      { id: 2, coin_slug: 'ethereum', target_price: 3000, direction: 'below', triggered: true, triggered_at: '2026-06-15T12:00:00Z', created_at: '' },
    ]

    await store.reactivate(2)

    expect(store.items[0].triggered).toBe(true)  // item 1 unchanged
    expect(store.items[1].triggered).toBe(false)  // item 2 reactivated
  })

  it('rethrows on API failure', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockRejectedValue({ data: { detail: 'You can have at most 10 active alerts' } })

    const store = useAlertStore()
    store.items = [{ id: 2, coin_slug: 'ethereum', target_price: 3000, direction: 'below', triggered: true, triggered_at: '2026-06-15T12:00:00Z', created_at: '' }]

    await expect(store.reactivate(2)).rejects.toBeDefined()
    expect(store.items[0].triggered).toBe(true)  // unchanged on failure
  })
})

// ── remove ────────────────────────────────────────────────────────────────────

describe('remove', () => {
  it('calls DELETE and removes item from list', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockResolvedValue(undefined)

    const store = useAlertStore()
    store.items = [
      { id: 1, coin_slug: 'bitcoin', target_price: 65000, direction: 'above', triggered: false, triggered_at: null, created_at: '' },
      { id: 2, coin_slug: 'ethereum', target_price: 3000, direction: 'below', triggered: false, triggered_at: null, created_at: '' },
    ]

    await store.remove(1)

    expect(store.items).toHaveLength(1)
    expect(store.items[0].id).toBe(2)
    expect(auth.authFetch).toHaveBeenCalledWith('/api/alerts/1', expect.objectContaining({ method: 'DELETE' }))
  })

  it('does not modify list if API call fails', async () => {
    const auth = setupAuth()
    vi.spyOn(auth, 'authFetch').mockRejectedValue(new Error('not found'))

    const store = useAlertStore()
    store.items = [
      { id: 1, coin_slug: 'bitcoin', target_price: 65000, direction: 'above', triggered: false, triggered_at: null, created_at: '' },
    ]

    await expect(store.remove(1)).rejects.toThrow()
    expect(store.items).toHaveLength(1)  // not removed on failure
  })
})
