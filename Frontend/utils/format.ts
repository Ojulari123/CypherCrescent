export function num(v: unknown, fallback = 0): number {
  if (v === null || v === undefined || v === '') return fallback
  const n = typeof v === 'number' ? v : parseFloat(String(v))
  return Number.isFinite(n) ? n : fallback
}

export function fmtUsd(n: number, max = 2): string {
  return n.toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: Math.min(2, max),
    maximumFractionDigits: max,
  })
}

// Price formatter that keeps precision for sub-dollar coins.
export function fmtPrice(n: number): string {
  if (n > 0 && n < 1) return fmtUsd(n, 6)
  return fmtUsd(n, 2)
}

export function fmtNum(n: number, max = 4): string {
  return n.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: max })
}

export function fmtPct(n: number): string {
  return `${n >= 0 ? '+' : ''}${n.toFixed(2)}%`
}

export function fmtCompact(n: number): string {
  if (n >= 1e12) return `$${(n / 1e12).toFixed(2)}T`
  if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`
  if (n >= 1e6) return `$${(n / 1e6).toFixed(2)}M`
  if (n >= 1e3) return `$${(n / 1e3).toFixed(2)}K`
  return fmtUsd(n, 0)
}

export function fmtDateTime(iso: string): string {
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' })
}

export function prettyEvent(event: string): string {
  return event.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

export const UP = '#16a34a'
export const DOWN = '#dc2626'
