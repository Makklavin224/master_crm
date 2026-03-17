# Technology Stack

**Project:** Master-CRM (multi-messenger CRM for self-employed professionals)
**Researched:** 2026-03-17

## Recommended Stack

### Frontend — Mini App (Shared codebase for TG / MAX / VK)

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| React | ^18.2 | UI framework | De facto standard for all three mini-app platforms. TG official templates use React, VK VKUI is React-based, MAX max-ui is React-based. | HIGH |
| TypeScript | ^5.4 | Type safety | Catches integration bugs across three messenger SDKs at compile time. Non-negotiable for a multi-platform project. | HIGH |
| Vite | ^6.x | Build tool | Sub-second HMR, native ESM, tree-shaking. Official TG Mini App templates use Vite. Produces small bundles critical for mini-app cold start. | HIGH |
| @telegram-apps/sdk-react | ^3.3 | TG Mini App bridge | Official SDK from Telegram team (tma.js). Provides hooks for initData, themeParams, viewport, back button, haptic feedback. | HIGH |
| @vkontakte/vk-bridge | ^2.15 | VK Mini App bridge | Official VK bridge library. Required for all VK Mini Apps API calls (getUserInfo, payments, storage). Actively maintained (updated Feb 2026). | HIGH |
| @maxhub/max-ui | latest | MAX Mini App UI + bridge | Official MAX messenger UI kit (React + TypeScript). Provides Panel, Button, and other components. Storybook docs at max-messenger.github.io/max-ui. | MEDIUM |
| Zustand | ^5.x | Client state management | 1KB, no boilerplate, hooks-based. Perfect for mini-app where bundle size matters. Zustand + TanStack Query covers 100% of state needs. | HIGH |
| @tanstack/react-query | ^5.90 | Server state / data fetching | Caching, background refetch, optimistic updates. Eliminates manual loading/error states. 80% adoption in new React apps per 2025 State of JS. | HIGH |
| Tailwind CSS | ^4.x | Styling | Utility-first, mobile-first by default. Tree-shakes to <10KB. No runtime overhead. Perfect for mini-apps where load time is critical. | HIGH |
| react-day-picker | ^9.x | Calendar / date picking | 6M+ weekly downloads, lightweight, accessible, customizable. Foundation of shadcn calendar. Use for booking slot selection UI. | HIGH |
| dayjs | ^1.11 | Date manipulation | 2KB alternative to Moment.js. Handles timezone, locale (ru), formatting for booking system. | HIGH |

### Frontend — Web Admin Panel

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| React | ^18.2 | UI framework (shared with mini-app) | Same framework = shared components, types, API clients between mini-app and admin panel. | HIGH |
| Vite | ^6.x | Build tool | Same tooling as mini-app. One team, one build system. | HIGH |
| Ant Design | ^5.x | Admin UI components | Battle-tested admin component library. Table, Form, DatePicker, Calendar, Drawer, Modal — all out of the box. 90K+ GitHub stars. Better for admin panels than shadcn (which requires building every component). | HIGH |
| @tanstack/react-query | ^5.90 | Server state | Same library as mini-app. Shared API hooks. | HIGH |
| @tanstack/react-router | ^1.x | Routing | Type-safe routing with search params. Better DX than react-router for admin panels with complex URL state (filters, pagination). | MEDIUM |
| Zustand | ^5.x | Client state | Shared with mini-app codebase. | HIGH |

### Backend — Core API

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python | 3.12+ | Runtime | Stable, performant, excellent async support. FastAPI requires >=3.10, but 3.12 has best performance. | HIGH |
| FastAPI | ^0.135 | Web framework | Async-native, auto-generated OpenAPI docs, Pydantic validation, dependency injection. Industry standard for Python async APIs. Latest: 0.135.1 (Mar 2026). | HIGH |
| Pydantic | ^2.12 | Data validation & serialization | Core of FastAPI. V2 has 5-50x performance boost over V1. Validates all request/response schemas. | HIGH |
| Uvicorn | ^0.30 | ASGI server | Standard production server for FastAPI. Use with `--workers` for multiprocessing or behind Gunicorn. | HIGH |
| Gunicorn | ^22.x | Process manager | Manages Uvicorn workers in production. `gunicorn -w 4 -k uvicorn.workers.UvicornWorker`. | HIGH |

### Backend — Database

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| PostgreSQL | 16+ | Primary database | Relational data (bookings, clients, services, payments) with JSONB for flexible metadata. Rock-solid for transactional workloads. | HIGH |
| SQLAlchemy | ^2.0 | ORM + query builder | Async support via `create_async_engine`. Type-safe queries, relationship loading, migration support via Alembic. The combined SQLAlchemy 2.0 + asyncpg pattern is the standard for FastAPI+PG in 2025-2026. | HIGH |
| asyncpg | ^0.30 | PostgreSQL async driver | 5x faster than psycopg3 in benchmarks. Native asyncio, optimized C implementation. Used as backend for SQLAlchemy async engine. | HIGH |
| Alembic | ^1.14 | Database migrations | Only migration tool for SQLAlchemy. Supports async via `async_engine_from_config`. Auto-generates migrations from model changes. | HIGH |
| Redis | ^7.x | Cache + task broker + sessions | Cache booking slot availability (hot path), task queue broker for ARQ, rate limiting, session storage. | HIGH |

### Backend — Bot Frameworks

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| aiogram | ^3.26 | Telegram Bot API | The standard async TG bot framework in Python. 3.26.0 supports Bot API 9.4 (Feb 2026). Router-based architecture, FSM, middleware system. Battle-tested in RU/CIS ecosystem. | HIGH |
| maxapi | ^0.9.16 | MAX Bot API | Official-community library for MAX messenger bots. Supports polling + webhook modes. Latest: 0.9.16 (Mar 2026). Most actively maintained of the MAX bot libraries. | MEDIUM |
| vkbottle | ^4.7 | VK Bot API | Customizable async VK API framework. 4.7.0 (Feb 2026). Router-based, middleware, state management. The standard choice for VK bots in Python. | HIGH |

### Backend — Payments & Tax

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Custom Robokassa integration | N/A | Payment processing | Robokassa API is simple (form URL with HMAC signature). Build a thin wrapper (~200 lines) rather than depending on unmaintained third-party libs. Endpoints: payment URL generation, ResultURL callback handler, status check. | HIGH |
| aiohttp | ^3.x | HTTP client for Robokassa calls | Async HTTP client for Robokassa API callbacks and status checks. Already a dependency of aiogram. | HIGH |

**Note on Robokassa libraries:** Existing Python libraries (`robokassa` 1.0.8, `aiorobokassa`) are limited to payment link generation. They do not cover Robochecks (fiscalization for self-employed). The Robokassa API for payments is simple enough (HMAC-signed URL + 3 callback endpoints) that a custom integration is more maintainable than wrapping a thin third-party lib. For Robochecks, you will need to implement the fiscalization API directly from Robokassa docs.

### Backend — Task Queue

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| ARQ | ^0.26 | Async task queue | Built for asyncio from the ground up. Natural fit for FastAPI. Handles: appointment reminders (24h/2h), payment expiry checks, Robochecks callback retries. Uses Redis as broker. Lightweight — no heavy Celery infrastructure needed. | MEDIUM |

**Why not Celery:** Celery is sync-first, requires significant boilerplate, and is overkill for this project's task volume. ARQ is async-native, uses Redis (already in stack), and handles scheduled tasks (cron-like) natively.

**Why not Taskiq:** Taskiq (latest Dec 2025) has excellent FastAPI integration and is arguably the more "correct" choice for 2026. However, ARQ is simpler, better documented, and sufficient for the task volume of this project. Consider Taskiq if task complexity grows significantly.

### Infrastructure

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Docker | 25+ | Containerization | Reproducible builds, isolation between services. Standard for VPS deployment. | HIGH |
| Docker Compose | 2.x | Multi-container orchestration | Single `docker-compose.yml` manages: API, TG bot, MAX bot, VK bot, PostgreSQL, Redis, Caddy. Simple, no K8s overhead for single VPS. | HIGH |
| Caddy | ^2.8 | Reverse proxy + HTTPS | Automatic Let's Encrypt certificates, zero-config HTTPS, 3-line config vs 50+ for Nginx. Docker-native with label-based proxy. Perfect for VPS where you want "just works" SSL. | HIGH |
| GitHub Actions | N/A | CI/CD | Free for public repos, generous for private. SSH deploy to VPS, run tests, build Docker images. | HIGH |

**Why Caddy over Nginx:** Caddy automatically manages SSL certificates (Let's Encrypt), supports HTTP/2 and HTTP/3 out of the box, and requires 3 lines of config for a reverse proxy vs 50+ for Nginx + certbot. For a solo developer on a VPS, the operational simplicity is worth the negligible performance difference.

### Monitoring & Observability

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Sentry | latest | Error tracking | Free tier covers small projects. Python + JS SDKs. Catches unhandled exceptions in API, bots, and mini-apps. | HIGH |
| structlog | ^24.x | Structured logging (Python) | JSON-formatted logs for easy parsing. Context-aware (request_id, user_id). Works with Python stdlib logging. | MEDIUM |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| ORM | SQLAlchemy 2.0 + asyncpg | SQLModel | SQLModel is a thin wrapper over SQLAlchemy, adds another abstraction layer, lags behind SQLAlchemy releases. Use SQLAlchemy directly for full control. |
| ORM | SQLAlchemy 2.0 + asyncpg | Raw asyncpg | Raw asyncpg is 5x faster but no migrations, no relationship loading, no schema validation. Booking/CRM domain has complex relations — ORM pays for itself. |
| State mgmt | Zustand | Redux Toolkit | Redux is 10x more boilerplate. Mini-app state is simple (user, booking flow, cart). Zustand's hook-based API fits perfectly. |
| Task queue | ARQ | Celery | Celery is sync-first, requires dedicated workers, complex config. ARQ is async-native, uses same Redis, simpler for our task volume. |
| Task queue | ARQ | Taskiq | Taskiq is newer and has better FastAPI integration, but ARQ is simpler and sufficient. Revisit if needs grow. |
| Reverse proxy | Caddy | Nginx | Nginx requires manual certbot setup, 50+ lines of config, no auto-HTTPS. Caddy does all this in 3 lines. |
| Admin UI | Ant Design | React Admin / Refine | React Admin is opinionated about data providers and adds its own abstraction. Ant Design gives raw components — more flexibility for custom admin workflows (schedule grid, booking timeline). |
| Admin UI | Ant Design | shadcn/ui | shadcn requires building every component from primitives. Ant Design has Table, Calendar, Form, Modal ready to use — faster for admin panel development. |
| MAX bot | maxapi | aiomax | aiomax (last update Nov 2025) has aiogram-like API but lower community adoption. maxapi (update Mar 2026) is more actively maintained and official-community supported. |
| MAX bot | maxapi | max-botapi-python | max-botapi-python (last update Jul 2025) is stale compared to maxapi. |
| TG bot | aiogram 3.x | python-telegram-bot | python-telegram-bot is sync-first (ptb v20 has async but it's not native). aiogram is async from the ground up, dominant in RU/CIS ecosystem, better middleware/router architecture. |
| VK bot | vkbottle | vk_api | vk_api is sync-only. vkbottle is async, actively maintained, has proper router/middleware architecture matching aiogram's patterns. |
| Python driver | asyncpg | psycopg3 async | asyncpg is 5x faster than psycopg3 in official benchmarks. Both work with SQLAlchemy async, but asyncpg has better raw performance. |
| Data fetching | TanStack Query | SWR | TanStack Query has better devtools, more features (mutations, infinite queries, suspense), larger community. SWR is lighter but lacks mutation support. |
| Calendar | react-day-picker | react-big-calendar | react-big-calendar is for event/scheduling views (like Google Calendar). For date slot *picking* in a booking flow, react-day-picker is lighter and more appropriate. Use react-big-calendar only for the admin panel's schedule view if needed. |

## Monorepo Structure

Use a **pnpm workspace monorepo** for the frontend to share code between mini-app and admin panel:

```
packages/
  shared/          # Shared types, API client, utils
  mini-app/        # React mini-app (TG/MAX/VK)
  admin/           # React admin panel
```

**Why pnpm:** Faster installs, strict dependency resolution, native workspace support. npm/yarn workspaces work too but pnpm is the 2025-2026 standard for monorepos.

## Project Structure (Backend)

```
backend/
  alembic/              # Database migrations
  app/
    api/
      v1/
        bookings.py     # Booking endpoints
        clients.py      # Client management
        services.py     # Service catalog
        payments.py     # Payment webhooks
        schedule.py     # Master schedule
        auth.py         # Authentication
    bots/
      telegram/         # aiogram handlers, routers, middlewares
      max/              # maxapi handlers
      vk/               # vkbottle handlers
      common/           # Shared notification router
    core/
      config.py         # Settings via pydantic-settings
      security.py       # JWT, HMAC verification
      database.py       # SQLAlchemy async engine, session
    models/             # SQLAlchemy models
    schemas/            # Pydantic request/response schemas
    services/           # Business logic layer
      booking_service.py
      payment_service.py
      notification_service.py
      robokassa_service.py
    tasks/              # ARQ task definitions
      reminders.py
      payment_checks.py
    main.py             # FastAPI app factory
  docker-compose.yml
  Dockerfile
  pyproject.toml        # Dependencies via Poetry or uv
```

## Installation

### Backend

```bash
# Using uv (recommended over pip/poetry in 2026)
uv init master-crm-backend
uv add fastapi[standard] uvicorn gunicorn
uv add sqlalchemy[asyncio] asyncpg alembic
uv add pydantic pydantic-settings
uv add aiogram maxapi vkbottle
uv add redis arq
uv add aiohttp httpx
uv add structlog sentry-sdk[fastapi]
uv add python-jose[cryptography] passlib[bcrypt]

# Dev dependencies
uv add --dev pytest pytest-asyncio httpx ruff mypy
```

### Frontend (Mini-App)

```bash
pnpm create vite mini-app --template react-ts
cd mini-app
pnpm add @telegram-apps/sdk-react @vkontakte/vk-bridge @maxhub/max-ui
pnpm add zustand @tanstack/react-query
pnpm add react-day-picker dayjs
pnpm add -D tailwindcss @tailwindcss/vite
```

### Frontend (Admin Panel)

```bash
pnpm create vite admin --template react-ts
cd admin
pnpm add antd @ant-design/icons
pnpm add zustand @tanstack/react-query @tanstack/react-router
pnpm add dayjs
pnpm add -D tailwindcss @tailwindcss/vite
```

## Docker Compose (Production)

```yaml
services:
  api:
    build: ./backend
    command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    env_file: .env
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_healthy }

  tg-bot:
    build: ./backend
    command: python -m app.bots.telegram
    env_file: .env
    depends_on: [api]

  max-bot:
    build: ./backend
    command: python -m app.bots.max
    env_file: .env
    depends_on: [api]

  vk-bot:
    build: ./backend
    command: python -m app.bots.vk
    env_file: .env
    depends_on: [api]

  worker:
    build: ./backend
    command: arq app.tasks.WorkerSettings
    env_file: .env
    depends_on: [db, redis]

  db:
    image: postgres:16-alpine
    volumes: [pgdata:/var/lib/postgresql/data]
    environment:
      POSTGRES_DB: mastercrm
      POSTGRES_USER: mastercrm
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mastercrm"]

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

  caddy:
    image: caddy:2-alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data

volumes:
  pgdata:
  caddy_data:
```

## Version Pinning Strategy

- **Pin major+minor** for critical dependencies (FastAPI, SQLAlchemy, aiogram)
- **Pin major** for UI libraries (React, Ant Design, Tailwind)
- **Use latest** for rapidly-evolving messenger SDKs (@telegram-apps/sdk-react, @maxhub/max-ui) but test before upgrading
- **Lock file** (`uv.lock` / `pnpm-lock.yaml`) committed to git always

## Sources

- FastAPI 0.135.1: [PyPI](https://pypi.org/project/fastapi/) | [Official Docs](https://fastapi.tiangolo.com/)
- aiogram 3.26.0: [PyPI](https://pypi.org/project/aiogram/) | [Docs](https://docs.aiogram.dev/)
- maxapi 0.9.16: [PyPI](https://pypi.org/project/maxapi/)
- vkbottle 4.7.0: [PyPI](https://pypi.org/project/vkbottle/) | [GitHub](https://github.com/vkbottle/vkbottle)
- @telegram-apps/sdk-react: [npm](https://www.npmjs.com/package/@telegram-apps/sdk-react) | [Docs](https://docs.telegram-mini-apps.com/packages/telegram-apps-sdk-react/2-x)
- @vkontakte/vk-bridge 2.15.10: [npm](https://www.npmjs.com/package/@vkontakte/vk-bridge)
- @maxhub/max-ui: [GitHub](https://github.com/max-messenger/max-ui) | [npm](https://www.npmjs.com/package/@maxhub/max-ui)
- VKUI 7.11.3: [npm](https://www.npmjs.com/package/@vkontakte/vkui) | [GitHub](https://github.com/VKCOM/VKUI)
- SQLAlchemy 2.0 + asyncpg: [Performance comparison](https://dasroot.net/posts/2026/02/python-postgresql-sqlalchemy-asyncpg-performance-comparison/)
- Robokassa API: [Official Docs](https://docs.robokassa.ru/) | [Robochecks for self-employed](https://robokassa.com/online-check/robocheck-smz/)
- Caddy: [Official site](https://caddyserver.com/)
- TanStack Query 5.90: [Official](https://tanstack.com/query/latest)
- Zustand: [npm](https://www.npmjs.com/package/zustand)
- Ant Design 5.x: [Official](https://ant.design/)
- Tailwind CSS 4.x: [Official](https://tailwindcss.com/)
- ARQ: [GitHub](https://github.com/samuelcolvin/arq)
- Docker Compose FastAPI patterns: [FastAPI docs](https://fastapi.tiangolo.com/deployment/docker/) | [KhueApps guide](https://www.khueapps.com/blog/article/setup-docker-compose-for-fastapi-postgres-redis-and-nginx-caddy)
