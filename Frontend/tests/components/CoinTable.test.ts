import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { useWatchlistStore } from '~/stores/watchlist'
import { usePortfolioStore } from '~/stores/portfolio'
import CoinTable from '~/components/CoinTable.vue'

const ROWS = [
  {
    id: 'bitcoin', symbol: 'BTC', name: 'Bitcoin', image: null, market_cap_rank: 1,
    current_price: 60000, market_cap: 1_300_000_000_000,
    price_change_percentage_1h: 0.5, price_change_percentage_24h: 2.3, price_change_percentage_7d: 5.1,
  },
  {
    id: 'ethereum', symbol: 'ETH', name: 'Ethereum', image: null, market_cap_rank: 2,
    current_price: 3000, market_cap: 360_000_000_000,
    price_change_percentage_1h: -0.2, price_change_percentage_24h: 1.5, price_change_percentage_7d: 3.2,
  },
  {
    id: 'solana', symbol: 'SOL', name: 'Solana', image: null, market_cap_rank: 5,
    current_price: 150, market_cap: null,
    price_change_percentage_1h: null, price_change_percentage_24h: -1.2, price_change_percentage_7d: null,
  },
]

const GLOBAL = {
  stubs: {
    NuxtLink: { template: '<a :href="to"><slot /></a>', props: ['to'] },
    CoinIcon: { template: '<span />' },
    ChangeBadge: { template: '<span />' },
  },
}

function mountTable(rows = ROWS, emptyHint?: string) {
  const props: Record<string, any> = { rows }
  if (emptyHint !== undefined) props.emptyHint = emptyHint
  return mount(CoinTable, { props, global: GLOBAL })
}

/** Find the <th> in <thead> whose text contains `label`. */
function thFor(wrapper: ReturnType<typeof mount>, label: string) {
  return wrapper.findAll('thead th').find((th) => th.text().includes(label))!
}

// ── Default sort ───────────────────────────────────────────────────────────────

describe('default sort', () => {
  it('orders rows by market cap descending out of the box', () => {
    const wrapper = mountTable()
    const rows = wrapper.findAll('tbody tr')
    expect(rows[0].text()).toContain('Bitcoin')
    expect(rows[1].text()).toContain('Ethereum')
    expect(rows[2].text()).toContain('Solana')
  })

  it('marks Market Cap header aria-sort="descending" by default', () => {
    const wrapper = mountTable()
    expect(thFor(wrapper, 'Market Cap').attributes('aria-sort')).toBe('descending')
  })

  it('marks non-active column headers aria-sort="none" by default', () => {
    const wrapper = mountTable()
    expect(thFor(wrapper, 'Price').attributes('aria-sort')).toBe('none')
    expect(thFor(wrapper, '24h').attributes('aria-sort')).toBe('none')
  })
})

// ── Sort interaction ───────────────────────────────────────────────────────────

describe('sort interaction', () => {
  it('toggles the active column to ascending on a second click', async () => {
    const wrapper = mountTable()
    await thFor(wrapper, 'Market Cap').find('button')!.trigger('click')
    expect(thFor(wrapper, 'Market Cap').attributes('aria-sort')).toBe('ascending')
  })

  it('resets to descending and clears the old column when switching columns', async () => {
    const wrapper = mountTable()
    // Make market cap ascending first
    await thFor(wrapper, 'Market Cap').find('button')!.trigger('click')
    // Switch to Price
    await thFor(wrapper, 'Price').find('button')!.trigger('click')
    expect(thFor(wrapper, 'Price').attributes('aria-sort')).toBe('descending')
    expect(thFor(wrapper, 'Market Cap').attributes('aria-sort')).toBe('none')
  })

  it('always puts null-metric coins at the bottom regardless of sort direction', async () => {
    const wrapper = mountTable()
    // Toggle market cap → ascending (Solana still has null market_cap)
    await thFor(wrapper, 'Market Cap').find('button')!.trigger('click')
    const rows = wrapper.findAll('tbody tr')
    expect(rows[rows.length - 1].text()).toContain('Solana')
  })

  it('sorts by price descending when the Price column is clicked', async () => {
    const wrapper = mountTable()
    await thFor(wrapper, 'Price').find('button')!.trigger('click')
    const rows = wrapper.findAll('tbody tr')
    // $60,000 > $3,000 > $150
    expect(rows[0].text()).toContain('Bitcoin')
    expect(rows[1].text()).toContain('Ethereum')
    expect(rows[2].text()).toContain('Solana')
  })
})

// ── Watchlist ──────────────────────────────────────────────────────────────────

describe('watchlist', () => {
  it('calls watchlist.toggle with the correct slug when a star is clicked', async () => {
    const watchlist = useWatchlistStore()
    vi.spyOn(watchlist, 'toggle').mockResolvedValue(undefined)
    const wrapper = mountTable()
    // First data row is Bitcoin (highest market cap by default)
    await wrapper.findAll('button[aria-label="Toggle watchlist"]')[0].trigger('click')
    expect(watchlist.toggle).toHaveBeenCalledWith('bitcoin')
  })

  it('renders the star as filled for a watched coin', () => {
    const watchlist = useWatchlistStore()
    watchlist.items = [
      {
        id: 1, coin_slug: 'bitcoin', created_at: '', name: 'Bitcoin', symbol: 'BTC',
        image: null, current_price: null, market_cap: null,
        price_change_percentage_1h: null, price_change_percentage_24h: null, price_change_percentage_7d: null,
      },
    ] as any
    const wrapper = mountTable()
    const starBtn = wrapper.findAll('button[aria-label="Toggle watchlist"]')[0]
    expect(starBtn.find('svg').classes()).toContain('fill-amber-400')
  })

  it('renders the star as unfilled for an unwatched coin', () => {
    const wrapper = mountTable()
    const starBtn = wrapper.findAll('button[aria-label="Toggle watchlist"]')[0]
    expect(starBtn.find('svg').classes()).not.toContain('fill-amber-400')
  })
})

// ── HELD badge ─────────────────────────────────────────────────────────────────

describe('HELD badge', () => {
  it('shows the HELD badge for coins in the portfolio', () => {
    const portfolio = usePortfolioStore()
    portfolio.dashboard = {
      total_value: 0, total_cost: 0, total_pl: 0, total_pl_percent: 0,
      top_performer: null, worst_performer: null, market_data_available: true,
      holdings: [
        {
          id: 1, coin_slug: 'bitcoin', quantity: 1, buy_price: 50000,
          name: 'Bitcoin', symbol: 'BTC', image: null,
          current_price: 60000, market_cap: null, price_change_percentage_24h: null,
          value: 60000, cost_basis: 50000, pl: 10000, pl_percent: 20,
        },
      ],
    } as any
    const wrapper = mountTable()
    expect(wrapper.text()).toContain('HELD')
  })

  it('does not show the HELD badge when the portfolio is empty', () => {
    const wrapper = mountTable()
    expect(wrapper.text()).not.toContain('HELD')
  })
})

// ── Empty state ────────────────────────────────────────────────────────────────

describe('empty state', () => {
  it('shows the default hint when rows is empty', () => {
    const wrapper = mountTable([])
    expect(wrapper.text()).toContain('No coins to show.')
  })

  it('shows a custom emptyHint when provided', () => {
    const wrapper = mountTable([], 'Nothing in your watchlist yet.')
    expect(wrapper.text()).toContain('Nothing in your watchlist yet.')
  })
})
