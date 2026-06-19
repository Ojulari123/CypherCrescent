// App-facing types. Numeric fields the backend serializes as Decimal arrive as
// strings over JSON, so stores coerce them to `number` at the boundary (see num()).

export type ChartRange = '24h' | '7d' | '30d'

export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  display_name?: string | null
  email_verified: boolean
  two_factor_enabled: boolean
  profile_photo_url?: string | null
  created_at: string
  updated_at: string
}

export interface ActivityLog {
  id: number
  event: string
  ip_address?: string | null
  user_agent?: string | null
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

// POST /api/users/login can short-circuit into a 2FA challenge.
export interface TwoFactorChallenge {
  two_factor_required: true
  challenge_token: string
}

export type LoginResult = TokenResponse | TwoFactorChallenge

export interface Holding {
  id: number
  coin_slug: string
  quantity: number
  buy_price: number
  created_at?: string
  updated_at?: string
}

export interface CoinMarket {
  id: string
  symbol: string
  name: string
  image?: string | null
  market_cap_rank?: number | null
  current_price: number | null
  market_cap: number | null
  price_change_percentage_1h: number | null
  price_change_percentage_24h: number | null
  price_change_percentage_7d: number | null
}

export interface HoldingWithMarket {
  id: number
  coin_slug: string
  quantity: number
  buy_price: number
  name?: string | null
  symbol?: string | null
  image?: string | null
  current_price: number | null
  market_cap: number | null
  price_change_percentage_24h: number | null
  value: number | null
  cost_basis: number
  pl: number | null
  pl_percent: number | null
}

export interface Performer {
  coin_slug: string
  name?: string | null
  pl_percent: number
}

export interface Dashboard {
  total_value: number
  total_cost: number
  total_pl: number
  total_pl_percent: number
  top_performer?: Performer | null
  worst_performer?: Performer | null
  holdings: HoldingWithMarket[]
  market_data_available: boolean
}

export interface ChartPoint {
  timestamp: number
  price: number
}

export interface ChartResponse {
  coin_id: string
  range: string
  days: number
  points: ChartPoint[]
}

export interface CoinSearchResult {
  id: string
  symbol: string
  name: string
  thumb?: string | null
  large?: string | null
  market_cap_rank?: number | null
}

export interface PriceAlert {
  id: number
  coin_slug: string
  target_price: number
  direction: 'above' | 'below'
  triggered: boolean
  triggered_at: string | null
  created_at: string
}

export interface WatchlistItem {
  id: number
  coin_slug: string
  created_at: string
  name?: string | null
  symbol?: string | null
  image?: string | null
  current_price: number | null
  market_cap: number | null
  price_change_percentage_1h: number | null
  price_change_percentage_24h: number | null
  price_change_percentage_7d: number | null
}
