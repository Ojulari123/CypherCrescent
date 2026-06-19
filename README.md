# CypherCrescent

A full-stack cryptocurrency portfolio tracker. Users register, record the coins they hold (quantity + buy price), track live value, profit/loss, and market data — powered by the [CoinGecko API](https://www.coingecko.com/en/api).

---

## Features

### Authentication & Security
- **JWT auth** with short-lived access tokens and long-lived refresh tokens — auto-refreshed silently in the background, no re-login until the refresh token expires
- **Refresh token rotation with reuse detection** — replaying a used token revokes the entire session across all devices
- **Email 2FA (opt-in)**
- **Email verification** on register; forgot-password / reset-password flow with time-limited tokens (regardless of 2FA)
- **Account activity log** — every security event (login, password change, 2FA toggle, logout) is recorded with IP + user-agent
- **Price Alert Functionality**

### Portfolio Management
- Add, edit, and delete coin holdings with quantity and buy price
- Dashboard shows total value, total cost, unrealised P&L (amount + %) and highlights the top and worst performers
- **Per-holding P&L** calculated live from current market price(values update whenever the market store refreshes)
- **Allocation breakdown** visualised as a donut chart
- **Performance area chart** across time on the dashboard

### Market Data
- Live prices, market cap, 24h % change, rank, and symbol pulled from **CoinGecko API**
- Markets page is **searchable, sortable, and paginated** with smooth skeleton loading between pages
- **Historical price charts** for 24h / 7d / 30d windows
- **Coin detail page** with full market stats, your position, price alerts, and a coin ↔ USD live converter

### Watchlist
- Star any coin to add it to your watchlist; unstar to remove(automatic rollback on failure)
- Watchlist items have live market data (price, 24h change) from the market cache

### Performance & UX
- **Redis caching** of all CoinGecko responses with configurable TTLs (market data 60s, search 600s, charts 300s)
- **Skeleton loading states** - No blank flashes during data fetches
- **Responsive design** — fully usable on mobile, tablet, and desktop; nav collapses to a bottom bar on small screens
- **Real-time updates** on watchlist and holdings. The UI reflects changes instantly while the API call is in flight
- **Debounced coin search** across markets and alert creation; avoids hammering the API on every keystroke
- **Rate limiting** (SlowAPI) on auth endpoints — 5 req/min per client

### Testing
- **133 backend tests** covering every endpoint — authentication, holdings, market, watchlist, alerts, profile, 2FA, activity log
- **101 frontend unit tests** (Vitest) — all 5 Pinia stores and 2 core components fully covered
- Backend suite uses in-memory SQLite and mocks all external IO (CoinGecko, Redis, Cloudinary, email) — no services needed to run tests
- Frontend tests use `happy-dom` and manual store stubs — no Nuxt runtime required


## Tech stack

- **Language:** Python 3.11
- **Framework:** FastAPI
- **Database:** PostgreSQL (Neon)
- **Migrations:** Alembic
- **Auth:** JWT (`python-jose`) + bcrypt password hashing
- **External API:** CoinGecko via its official Python SDK (`coingecko_sdk`)
- **Caching:** Redis
- **Rate limiting:** SlowAPI
- **Media:** Cloudinary (profile photos)
- **Email:** Resend (verification, password reset, 2FA codes)
- **Validation/config:** Pydantic v2 + pydantic-settings

---

## Project structure

```
CypherCrescent/
├── README.md
├── Frontend/                 
└── Backend/
    ├── main.py               # FastAPI app, CORS, routers, rate limiter
    ├── tables.py             # SQLAlchemy models (User, Holding, Watchlist) + engine/session
    ├── requirements.txt
    ├── alembic.ini
    ├── alembic/              # migration environment + versions
    ├── Config/
    │   └── config.py         # Settings (env vars), computed DATABASE_URL
    ├── Routes/               # API endpoints
    │   ├── user.py           # auth, profile, password
    │   ├── holding.py        # portfolio CRUD
    │   ├── market.py         # market data, search, historical chart
    │   ├── dashboard.py      # portfolio aggregates
    │   ├── watchlist.py      # watchlist CRUD
    │   └── alert.py          # price alerts CRUD + PATCH edit
    ├── Schemas/              # Pydantic enums/request/response models
    │   ├── userSchema.py
    │   ├── holdingSchema.py
    │   ├── marketSchema.py
    │   ├── watchlistSchema.py
    │   └── alertSchema.py
    ├── Utils/                # helpers (security, coingecko, redis_cache, email, etc.)
    └── Tests/                # pytest suite (in-memory SQLite, mocked external IO)
```

---

## Getting started

### Prerequisites

- Python 3.11+
- A PostgreSQL database (local or hosted)
- A running Redis instance
- A [CoinGecko API key](https://www.coingecko.com/en/api) (demo key works)
- A Cloudinary account (for profile photos)
- A [Resend](https://resend.com) API key (for verification & password-reset emails)

### Environment variables

Create a `.env` file inside `Backend/`

| Variable | Default | Description |
|----------|:--------:|---------|
| `NPGUSER`| — | Postgres user |
| `NPGPASSWORD`| — | Postgres password |
| `NPGDB`| — | Postgres database name |
| `NPGHOST`| — | Postgres host |
| `NPGPORT`| `5432` | Postgres port |
| `JWT_SECRET`| — | Secret used to sign JWTs |
| `JWT_ALGORITHM`| `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| `60` | Access-token lifetime (minutes) |
| `REFRESH_TOKEN_EXPIRE_DAYS`| `30` | Refresh-token lifetime (days) |
| `RESEND_API_KEY` | — | Resend API key for transactional email |
| `EMAIL_FROM` | `CypherCrescent <onboarding@resend.dev>` | From-address for outgoing email |
| `EMAIL_VERIFY_EXPIRE_MINUTES` |`60` | Email-verification token lifetime |
| `PASSWORD_RESET_EXPIRE_MINUTES` | `60` | Password-reset token lifetime |
| `OTP_EXPIRE_MINUTES` | `10` | Email 2FA / verification-code lifetime |
| `CYPHER_CRESCENT_CLOUDINARY_CLOUD_NAME` | — | Cloudinary cloud name |
| `CYPHER_CRESCENT_CLOUDINARY_API_KEY`| — | Cloudinary API key |
| `CYPHER_CRESCENT_CLOUDINARY_API_SECRET` | — | Cloudinary API secret |
| `COINGECKO_API_KEY` | — | CoinGecko demo API key (used via the official `coingecko_sdk`) |
| `REDIS_URL` | — | Redis connection URL, e.g. `redis://localhost:6379/0` |
| `MARKET_CACHE_TTL` | `60` | Cache TTL (s) for market data |
| `SEARCH_CACHE_TTL` | `600` | Cache TTL (s) for search results |
| `CHART_CACHE_TTL` | `300` | Cache TTL (s) for historical charts |
| `FRONTEND_URL` | `http://localhost:3000` | Frontend origin |

Example `.env`:

```env
NPGUSER=postgres
NPGPASSWORD=changeme
NPGDB=cyphercrescent
NPGHOST=localhost
NPGPORT=5432

JWT_SECRET=replace-with-a-long-random-string

RESEND_API_KEY=re_your_key_here
EMAIL_FROM=CypherCrescent <onboarding@resend.dev>

CYPHER_CRESCENT_CLOUDINARY_CLOUD_NAME=your-cloud
CYPHER_CRESCENT_CLOUDINARY_API_KEY=your-key
CYPHER_CRESCENT_CLOUDINARY_API_SECRET=your-secret

COINGECKO_API_KEY=your-coingecko-key
REDIS_URL=redis://localhost:6379/0
```

### Install & run

```bash
cd Backend

# 1. create & activate a virtual environment (optional)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. install dependencies
pip install -r requirements.txt

# 3. create/get .env (see above)

# 4. apply database migrations
alembic upgrade head

# 5. start the API
uvicorn main:app --reload
```

### Database & migrations

The schema is managed with Alembic.

```bash
alembic upgrade head                          # apply all migrations
alembic revision --autogenerate -m "message"  # create a new migration after model changes
alembic downgrade -1                           # roll back one migration
```

---

## Running the tests

The suite uses an in-memory SQLite database and mocks all external IO (CoinGecko, Redis, Cloudinary, SMTP), so it needs no network or running services.

```bash
cd Backend
pytest            # run everything (168 tests)
pytest -v         # verbose
pytest Tests/test_watchlist.py    # a single file
```

---

## Caching

CoinGecko responses are cached in Redis to stay within rate limits and reduce latency:

- Market data — `MARKET_CACHE_TTL` (default 60s)
- Search results — `SEARCH_CACHE_TTL` (default 600s)
- Historical charts — `CHART_CACHE_TTL` (default 300s)

## API documentation

Interactive, auto-generated docs are available while the server runs:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI schema:** http://localhost:8000/openapi.json

Use the **Authorize** button in Swagger (via `/api/users/token`) to call protected endpoints.

---

## Frontend

### Tech stack

| | |
|---|---|
| **Framework** | Nuxt 3 |
| **UI language** | Vue 3 + TypeScript |
| **Styling** | Tailwind CSS v4 |
| **State management** | Pinia |
| **Icons** | Lucide Vue Next |
| **Utilities** | VueUse |

### Pages

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | Portfolio stat cards, area chart, donut allocation, sortable holdings table |
| Markets | `/markets` | Live coin prices |
| Watchlist | `/watchlist` | Starred coins with live market data |
| Coin detail | `/coins/:id` | Full coin page with 24h / 7d / 30d price chart, active alerts panel, coin ↔ USD converter |
| Price Alerts | `/alerts` | Manage all price alerts; active and triggered history, create / edit / delete |
| Settings | `/settings` | Profile info, photo upload, email verification, password change, 2FA, activity log |
| Login | `/login` | JWT login |
| Register | `/register` | Account creation |
| Forgot / Reset password | `/forgot-password`, `/reset-password` | Email-token password reset flow |
| Verify email | `/verify-email` | Email verification landing page |

### State management (Pinia stores)

| Store | Responsibility |
|-------|---------------|
| `auth` | User session, tokens, login / logout / register |
| `portfolio` | Holdings, dashboard aggregates, performance chart series |
| `market` | Top coins, search results, coin data cache |
| `watchlist` | Watched coins with live market data |
| `alert` | Price alerts — load, create, update, delete; active / triggered getters, per-coin helpers |
| `ui` | Theme, global search query, modal state, toasts |

### Environment variables

Create a `.env` file inside `Frontend/`:

```env
NUXT_PUBLIC_API_BASE=http://localhost:8000
```

| Variable | Default | Description |
|----------|---------|-------------|
| `NUXT_PUBLIC_API_BASE` | `http://localhost:8000` | Backend API base URL — set to your deployed backend in production |

### Install & run

```bash
cd Frontend

# 1. install dependencies
npm install

# 2. create .env (see above)

# 3. generate Nuxt types
npx nuxi prepare

# 4. start dev server
npm run dev
```

```bash
# build for production
npm run build
npm run preview
```

### Project structure

```
Frontend/
├── app.vue                  # root component
├── nuxt.config.ts           # Nuxt config — SPA mode, Tailwind, runtime config
├── pages/                   # file-based routing
│   ├── index.vue            # Dashboard
│   ├── markets.vue          # Markets
│   ├── watchlist.vue        # Watchlist
│   ├── settings.vue         # Settings
│   ├── coins/[id].vue       # Coin detail
│   ├── login.vue
│   ├── register.vue
│   ├── forgot-password.vue
│   ├── reset-password.vue
│   └── verify-email.vue
├── components/              # reusable UI components
├── stores/                  # Pinia stores (auth, portfolio, market, watchlist, alert, ui)
├── layouts/                 # default (app shell) + auth layouts
├── middleware/              # route guards
├── utils/                   # format helpers, coin utilities
├── types/                   # TypeScript type definitions
└── assets/css/main.css      # global styles + Tailwind entry
```

---

## Authors

Adeoluwa Ojulari
