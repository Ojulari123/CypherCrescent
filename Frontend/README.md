# Cypher Crescent — Frontend

A Nuxt 3 + Vue 3 crypto portfolio tracker, built against the Cypher Crescent FastAPI backend.
UI ported verbatim from the MagicPath design, with a CoinMarketCap-style top nav, dashboard,
markets, watchlist, and full coin detail pages.

## Stack

- **Nuxt 3** (Vue 3, `<script setup>` + TypeScript)
- **Pinia** for state (`auth`, `market`, `portfolio`, `watchlist`, `ui`)
- **Tailwind CSS v4** (via `@tailwindcss/vite`, tokens in `assets/css/main.css`)
- **lucide-vue-next** icons, **@vueuse/core** utilities
- **Hand-rolled SVG charts** (no charting dependency): `AreaChart`, `Sparkline`, `DonutChart`

## Requirements

- Node 18+ (developed on Node 22)
- The backend running and reachable (default `http://localhost:8000`)

## Setup

```bash
cd Frontend
npm install

# point at your backend (optional — defaults to http://localhost:8000)
cp .env.example .env
# edit NUXT_PUBLIC_API_BASE if your API is elsewhere

npm run dev      # http://localhost:3000
```

> The backend's CORS is open (`allow_origins=["*"]`), so no extra config is needed for local dev.

### Scripts

```bash
npm run dev        # dev server with HMR
npm run build      # production build (.output/)
npm run preview    # preview the production build
```

## How it maps to the backend

| Feature | Endpoint(s) |
|---|---|
| Register / Login | `POST /api/users/register`, `POST /api/users/login` |
| 2FA challenge | login returns `{ two_factor_required, challenge_token }` → `POST /api/users/2fa/verify` |
| Token refresh | `POST /api/users/refresh` (automatic on 401, single-flight) |
| Email verification | `GET /api/users/verify-email?token=` (page `/verify-email`) |
| Forgot / reset password | `POST /api/users/forgot-password`, `POST /api/users/reset-password` |
| Current user | `GET /api/users/me` |
| Dashboard | `GET /api/dashboard` (totals, top/worst performer, holdings) |
| Holdings CRUD | `POST/GET/PATCH/DELETE /api/holdings` |
| Market data | `GET /api/market/coins?ids=…` |
| Search | `GET /api/market/search?q=…` |
| Historical chart | `GET /api/market/coins/{id}/chart?range=24h|7d|30d` |
| Watchlist | `POST/GET/DELETE /api/watchlist` |

Numeric fields the backend serializes as `Decimal` arrive as JSON strings and are coerced to
numbers at the store boundary (`utils/format.ts` → `num()`).

## Architecture

```
assets/css/main.css      Tailwind v4 + design tokens (light/dark)
types/api.ts             App-facing types mirroring the backend schemas
utils/format.ts          fmtUsd / fmtPrice / fmtCompact / num() coercion
utils/coins.ts           fallback colors + default Markets id set
stores/                  auth, market, portfolio, watchlist, ui (Pinia)
plugins/init.client.ts   restores theme + session on boot
middleware/auth.global   protects routes (client-enforced)
layouts/                 default (app shell) + auth (split brand panel)
components/              CoinIcon, ChangeBadge, charts, TopNav, tables, modals…
pages/                   login, register, verify-email, forgot/reset-password,
                         index (dashboard), markets, watchlist, coins/[id]
```

### Auth & protected routes

- Tokens persist in `localStorage`; `auth.authFetch()` attaches the `Bearer` access token and
  transparently refreshes once on a 401 (shared single-flight promise), then retries.
- `middleware/auth.global.ts` redirects unauthenticated users to `/login` and authenticated users
  away from the auth pages. Enforced on the client (where the token lives).

### Notes on derived data

- **Portfolio value chart**: the backend has no portfolio-timeseries endpoint, so the dashboard
  chart is built from real CoinGecko history — each holding's `/chart` × quantity, summed.
- **Global stats strip** and **market dominance** are derived from the coins currently loaded
  (the backend exposes no global-market endpoint) — never fabricated.
- **Markets list**: `/market/coins` requires explicit ids, so the page loads a curated id set and
  uses `/market/search` to discover additional coins as you type.
