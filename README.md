# CypherCrescent

A full-stack cryptocurrency portfolio tracker. Users register, record the coins they hold (quantity + buy price), track live value, profit/loss, and market data — powered by the [CoinGecko API](https://www.coingecko.com/en/api).

---

## Features

| Area | What it does |
|------|--------------|
| **Authentication** | Register, login, JWT-protected routes, email verification, password reset, change password, logout (token invalidation)
| **Holdings** | Add / view / update / delete holdings, scoped per user, with coin-id validation against CoinGecko 
| **Market data** | Live price, market cap, 24h change, name & symbol for any coins
| **Dashboard** | Total portfolio value, total cost, total P/L (%), top & worst performer 
| **Watchlist** | Add / remove / view watched coins, enriched with live market data
| **Historical chart** | Price history for 24h / 7d / 30d windows
| **Profile** | Update profile, upload/delete profile photo (Cloudinary)
| **Account activity** | View a log of security events (register, login, password change, 2FA changes, logout)

**Bonus / extras implemented:** Redis caching of CoinGecko responses, unit tests (133), request rate limiting (SlowAPI), database migrations (Alembic).

---

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
- **Email:** SMTP (verification + password reset)
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
    │   └── watchlist.py      # watchlist CRUD
    ├── Schemas/              # Pydantic enums/request/response models
    │   ├── userSchema.py
    │   ├── holdingSchema.py
    │   ├── marketSchema.py
    │   └── watchlistSchema.py
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
- SMTP credentials (for verification & password-reset emails)

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
| `SMTP_HOST` | — | SMTP server host |
| `SMTP_PORT` | — | SMTP server port |
| `SMTP_USER` | — | SMTP username |
| `SMTP_PASSWORD` | — | SMTP password |
| `EMAIL_FROM` | `""` | From-address for outgoing email |
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

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@example.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=you@example.com

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
pytest            # run everything (133 tests)
pytest -v         # verbose
pytest Tests/test_watchlist.py    # a single file
```

---

## Authentication

- Passwords are hashed with **bcrypt**; minimum length is **8 characters**.
- On **register** and **login** the API returns a **JWT access token** plus the user object.
- Send the token on protected requests:
  ```
  Authorization: Bearer <access_token>
  ```
- Login/register return a short-lived **access token** (`ACCESS_TOKEN_EXPIRE_MINUTES`, default 60) plus a long-lived **refresh token** (`REFRESH_TOKEN_EXPIRE_DAYS`, default 30). Send the access token on requests; when it expires, `POST /api/users/refresh` with `{ "refresh_token": ... }` returns a fresh pair — no re-login (and no 2FA) needed until the refresh token itself expires or is revoked.
- Access and refresh tokens are distinguished by a `type` claim; a refresh token can't be used as an access token (or vice versa).
- **Refresh tokens rotate with reuse detection.** Each refresh belongs to a session (tracked in Redis); calling `/refresh` issues a new token and invalidates the old one. If an already-used (e.g. stolen) refresh token is replayed, the whole session is revoked and that user must log in again. (Refresh therefore requires Redis to be available.)
- **Logout** bumps the user's token version, invalidating previously issued tokens. `POST /api/users/logout-all` does the same explicitly (signs out every device).
- A verification email is sent on registration; password reset is a request → email token → confirm flow.
- Auth endpoints are **rate-limited** to 5 requests/minute per client.

### Email two-factor authentication (2FA)

- **Opt-in** per user, off by default. Enable: `POST /api/users/2fa/enable` → emailed 6-digit code → `POST /api/users/2fa/enable/confirm`. Disable mirrors it under `/2fa/disable`.
- With 2FA on, **login is two-step**: `POST /api/users/login` returns `{ "two_factor_required": true, "challenge_token": ... }` and emails a code; exchange both at `POST /api/users/2fa/verify` for the access token.
- **Changing your password always requires an emailed code**, regardless of the 2FA setting: `PUT /api/users/me/password` (verifies current/new, sends code) → `PUT /api/users/me/password/verify` (`code` + `new_password`).
- Codes are 6 digits, single-use, expire after `OTP_EXPIRE_MINUTES`, capped at 5 attempts, and stored in Redis — so 2FA login and password changes require Redis to be available.

### Account activity

- `GET /api/users/activity` returns your 100 most recent security events (register, login, password change/reset, 2FA enable/disable, logout, email change), newest first, each with the IP and user-agent it came from.
- Recording is **best-effort** — a logging failure never blocks the action itself.

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

## Authors

Adeoluwa Ojulari
