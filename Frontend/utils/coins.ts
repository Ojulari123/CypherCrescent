// Brand colors for the fallback coin badge (used when the API image is missing)
// and the curated id set the Markets page loads (the backend's /market/coins
// requires explicit ids — there is no "list all by market cap" endpoint).

export const COIN_COLORS: Record<string, string> = {
  bitcoin: '#f7931a',
  ethereum: '#627eea',
  solana: '#14f195',
  'usd-coin': '#2775ca',
  tether: '#26a17b',
  chainlink: '#2a5ada',
  'avalanche-2': '#e84142',
  'matic-network': '#8247e5',
  polkadot: '#e6007a',
  cardano: '#0033ad',
  dogecoin: '#c2a633',
  ripple: '#23292f',
  'binancecoin': '#f3ba2f',
  tron: '#ef0027',
  litecoin: '#345d9d',
}

export function coinColor(slug: string): string {
  return COIN_COLORS[slug] ?? '#64748b'
}

// Default Markets watch universe (CoinGecko ids).
export const DEFAULT_MARKET_IDS = [
  'bitcoin',
  'ethereum',
  'tether',
  'binancecoin',
  'solana',
  'usd-coin',
  'ripple',
  'cardano',
  'avalanche-2',
  'dogecoin',
  'tron',
  'chainlink',
  'polkadot',
  'matic-network',
  'litecoin',
]

export const RANGES: Array<'24h' | '7d' | '30d'> = ['24h', '7d', '30d']
export const RANGE_LABEL: Record<string, string> = { '24h': '24H', '7d': '7D', '30d': '30D' }
