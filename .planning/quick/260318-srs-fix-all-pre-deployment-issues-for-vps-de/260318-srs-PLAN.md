---
phase: quick
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - frontend/Dockerfile
  - web/Dockerfile
  - backend/.dockerignore
  - frontend/.dockerignore
  - web/.dockerignore
  - docker-compose.yml
  - Caddyfile
  - .env.production
  - .env.example
  - .gitignore
  - frontend/src/stores/master-auth.ts
  - frontend/src/pages/client/BookingForm.tsx
autonomous: true
requirements: [DEPLOY-ALL]

must_haves:
  truths:
    - "frontend/Dockerfile and web/Dockerfile produce nginx-based production images (not dev servers)"
    - "docker-compose.yml runs API with 4 workers, auto-migration, healthchecks, restart policies"
    - "Caddyfile uses domain variable with automatic TLS and security headers"
    - ".env.production template contains every required variable with safe example values"
    - "Master auth token persists in localStorage across page reloads (frontend mini-app)"
    - "Phone validation rejects numbers that are not exactly 11 digits"
  artifacts:
    - path: "frontend/Dockerfile"
      provides: "Multi-stage build: node build -> nginx serve"
    - path: "web/Dockerfile"
      provides: "Multi-stage build: node build -> nginx serve, base /admin/"
    - path: "docker-compose.yml"
      provides: "Production-ready compose with healthchecks and migration entrypoint"
    - path: "Caddyfile"
      provides: "TLS-enabled reverse proxy with security headers"
    - path: ".env.production"
      provides: "Complete production env template"
    - path: "frontend/src/stores/master-auth.ts"
      provides: "localStorage persistence for master JWT"
    - path: "frontend/src/pages/client/BookingForm.tsx"
      provides: "Strict 11-digit Russian phone validation"
  key_links:
    - from: "docker-compose.yml"
      to: "backend/Dockerfile"
      via: "api service build context"
      pattern: "alembic upgrade head.*&&.*uvicorn"
    - from: "docker-compose.yml"
      to: "frontend/Dockerfile, web/Dockerfile"
      via: "nginx containers on ports 3000/3001"
    - from: "Caddyfile"
      to: "docker-compose services"
      via: "reverse_proxy directives"
---

<objective>
Fix all pre-deployment issues for Master CRM VPS deployment.

Purpose: The codebase uses dev-only Dockerfiles (pnpm dev), no .dockerignore, no TLS, no healthchecks, no auto-migration, missing env template, broken auth persistence, and loose phone validation. All must be fixed before deploying to production VPS.

Output: Production-ready Docker setup, TLS-configured Caddy, complete .env.production template, persistent master auth, strict phone validation.
</objective>

<execution_context>
@/Users/yannovak/.claude/get-shit-done/workflows/execute-plan.md
@/Users/yannovak/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@docker-compose.yml
@Caddyfile
@.env
@.env.example
@.gitignore
@frontend/Dockerfile
@web/Dockerfile
@backend/Dockerfile
@frontend/vite.config.ts (build.outDir = "dist")
@web/vite.config.ts (base: "/admin/", build.outDir = "dist")
@frontend/src/stores/master-auth.ts (no localStorage, token lost on reload)
@web/src/stores/auth.ts (reference: has safeGetItem/safeSetItem/safeRemoveItem + hydrate pattern)
@frontend/src/pages/client/BookingForm.tsx (phone validation: cleanedPhone.length < 12, should be !== 12)

<interfaces>
<!-- Key patterns the executor needs -->

From web/src/stores/auth.ts (reference for localStorage pattern):
```typescript
const TOKEN_KEY = "admin_token";
function safeGetItem(key: string): string | null { try { return localStorage.getItem(key); } catch { return null; } }
function safeSetItem(key: string, value: string): void { try { localStorage.setItem(key, value); } catch {} }
function safeRemoveItem(key: string): void { try { localStorage.removeItem(key); } catch {} }
// Store has hydrate() method that reads from localStorage on app start
```

From frontend/src/stores/master-auth.ts (current state):
```typescript
interface MasterAuthState {
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (initDataRaw: string) => Promise<boolean>;
  setToken: (token: string | null) => void;
  logout: () => void;
}
// masterApiRequest() reads token from useMasterAuth.getState()
```

From frontend/src/pages/client/BookingForm.tsx (phone validation):
```typescript
function cleanPhone(formatted: string): string {
  return "+" + formatted.replace(/\D/g, "");
}
// Current validation: cleanedPhone.length < 12 (allows 13+ digits)
// Fix: cleanedPhone.length !== 12 (exactly +7XXXXXXXXXX = 12 chars)
```

From backend main.py lifespan (migration context):
```python
# Alembic is available: backend/alembic/ directory with versions/
# Command: uv run alembic upgrade head
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Production Docker setup (Dockerfiles + .dockerignore + docker-compose)</name>
  <files>frontend/Dockerfile, web/Dockerfile, backend/.dockerignore, frontend/.dockerignore, web/.dockerignore, docker-compose.yml</files>
  <action>
1. **Rewrite frontend/Dockerfile** as multi-stage build:
   - Stage 1 "build": FROM node:20-alpine, corepack enable, WORKDIR /app, COPY package.json pnpm-lock.yaml, pnpm install --frozen-lockfile, COPY ., RUN pnpm build
   - Stage 2: FROM nginx:alpine, COPY --from=build /app/dist /usr/share/nginx/html, create inline nginx.conf that: listens on port 3000, serves /usr/share/nginx/html, has try_files $uri $uri/ /index.html (SPA fallback), gzip on
   - EXPOSE 3000

2. **Rewrite web/Dockerfile** as multi-stage build:
   - Same as frontend but: listens on port 3001, COPY --from=build /app/dist /usr/share/nginx/html
   - IMPORTANT: The web app uses `base: "/admin/"` in vite.config.ts, so the nginx location block should serve at root (Caddy handles the /admin prefix stripping)
   - EXPOSE 3001

3. **Create backend/.dockerignore**:
   ```
   __pycache__/
   *.pyc
   .venv/
   .env
   .git
   .mypy_cache/
   .pytest_cache/
   .ruff_cache/
   tests/
   *.egg-info/
   ```

4. **Create frontend/.dockerignore**:
   ```
   node_modules/
   dist/
   .git
   .env
   .env.local
   *.log
   ```

5. **Create web/.dockerignore** (same as frontend):
   ```
   node_modules/
   dist/
   .git
   .env
   .env.local
   *.log
   ```

6. **Update docker-compose.yml**:
   - **api service**: Remove `--reload` from command. Change command to: `sh -c "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4"`. Remove `volumes` bind mount (production doesn't need hot reload). Add `restart: unless-stopped`. Add healthcheck: `test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]` with interval 30s, timeout 10s, retries 3, start_period 40s.
   - NOTE: The /api/v1/health endpoint may not exist yet. Use a simpler check: `test: ["CMD-SHELL", "python -c 'import urllib.request; urllib.request.urlopen(\"http://localhost:8000/docs\")'"]` -- or even better, since curl may not be in the image, use: `test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/docs')\""]`. Actually simplest: add `curl` is not available in slim image. Use: `test: ["CMD-SHELL", "uv run python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/docs')\""]`
   - **frontend service**: Remove `volumes` and `command` (Dockerfile CMD handles it via nginx). Add `restart: unless-stopped`. Add healthcheck: `test: ["CMD", "curl", "-f", "http://localhost:3000/"]`, interval 30s, timeout 5s, retries 3.
   - **web service**: Same as frontend but port 3001. Add `restart: unless-stopped`. Add healthcheck.
   - **db service**: Add `restart: unless-stopped`. Keep existing healthcheck.
   - **caddy service**: Add `restart: unless-stopped`. Add `env_file: .env` (for DOMAIN variable). Add volume for caddy_config: `caddy_config:/config`.
   - Add `caddy_config` to volumes section.
   - Remove docker-compose.override.yml reference concerns -- the override file is for local dev and auto-merges.
  </action>
  <verify>
    <automated>cd /Users/yannovak/development/projects/master_crm && cat frontend/Dockerfile | grep -q "nginx" && cat web/Dockerfile | grep -q "nginx" && cat docker-compose.yml | grep -q "workers 4" && cat docker-compose.yml | grep -q "alembic upgrade head" && cat docker-compose.yml | grep -q "unless-stopped" && test -f backend/.dockerignore && test -f frontend/.dockerignore && test -f web/.dockerignore && echo "PASS"</automated>
  </verify>
  <done>Both frontend Dockerfiles are multi-stage (build+nginx), docker-compose has no --reload, runs 4 workers, auto-migrates with alembic, all services have restart:unless-stopped and healthchecks, .dockerignore files exist for all three services.</done>
</task>

<task type="auto">
  <name>Task 2: Caddyfile TLS + env config + .gitignore</name>
  <files>Caddyfile, .env.production, .env.example, .gitignore</files>
  <action>
1. **Rewrite Caddyfile** with TLS and security headers:
   ```
   {$DOMAIN} {
       # Security headers
       header {
           X-Content-Type-Options "nosniff"
           X-Frame-Options "SAMEORIGIN"
           Referrer-Policy "strict-origin-when-cross-origin"
           X-XSS-Protection "1; mode=block"
           -Server
       }

       # Enable gzip
       encode gzip

       # Admin panel
       handle /admin/* {
           uri strip_prefix /admin
           reverse_proxy web:3001
       }

       # Mini-app
       handle /app/* {
           uri strip_prefix /app
           reverse_proxy frontend:3000
       }

       # API
       handle /api/* {
           reverse_proxy api:8000
       }

       # Webhooks
       handle /webhook/* {
           reverse_proxy api:8000
       }

       # Default
       handle {
           reverse_proxy api:8000
       }
   }
   ```
   Caddy automatically handles TLS with Let's Encrypt when given a domain name (not :80). The {$DOMAIN} env var is read from the environment. No HTTP->HTTPS redirect block needed -- Caddy does this automatically when serving a domain with TLS.

2. **Create .env.production** with ALL required variables (generated example values for secrets):
   ```
   # === Core ===
   DEBUG=false
   DOMAIN=crm.example.com

   # === Database ===
   DATABASE_URL=postgresql+asyncpg://mastercrm_owner:CHANGE_ME_STRONG_PASSWORD@db:5432/mastercrm
   DATABASE_APP_URL=postgresql+asyncpg://app_user:CHANGE_ME_STRONG_PASSWORD@db:5432/mastercrm
   DB_ECHO=false
   DB_PASSWORD=CHANGE_ME_STRONG_PASSWORD
   APP_USER_PASSWORD=CHANGE_ME_STRONG_PASSWORD

   # === Auth ===
   JWT_SECRET_KEY=a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ENCRYPTION_KEY=CHANGE_ME_generate_with_python_-c_from_cryptography.fernet_import_Fernet;print(Fernet.generate_key().decode())

   # === CORS ===
   ALLOWED_ORIGINS=["https://crm.example.com"]

   # === Telegram Bot ===
   TG_BOT_TOKEN=
   BASE_WEBHOOK_URL=https://crm.example.com
   WEB_ADMIN_URL=https://crm.example.com/admin

   # === MAX Messenger ===
   MAX_BOT_TOKEN=
   MAX_BOT_ACCESS_TOKEN=

   # === VK ===
   VK_APP_ID=
   VK_APP_SECRET=
   VK_BOT_TOKEN=
   VK_CONFIRMATION_TOKEN=

   # === Robokassa ===
   ROBOKASSA_RESULT_URL=https://crm.example.com/api/v1/payments/robokassa/result
   ```

3. **Update .env.example** to match .env.production structure but with safe dev defaults:
   ```
   # === Core ===
   DEBUG=true
   DOMAIN=localhost

   # === Database ===
   DATABASE_URL=postgresql+asyncpg://mastercrm_owner:devpassword@db:5432/mastercrm
   DATABASE_APP_URL=postgresql+asyncpg://app_user:appuserpassword@db:5432/mastercrm
   DB_ECHO=false
   DB_PASSWORD=devpassword
   APP_USER_PASSWORD=appuserpassword

   # === Auth ===
   JWT_SECRET_KEY=change-me-in-production-use-openssl-rand-hex-32
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ENCRYPTION_KEY=HJfr7SJebm9ZFiE-afhJZ-GkYM3ZuM9ajUQqdaTOd9I=

   # === CORS ===
   ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:80"]

   # === Telegram Bot ===
   TG_BOT_TOKEN=
   BASE_WEBHOOK_URL=
   WEB_ADMIN_URL=http://localhost:3001

   # === MAX Messenger ===
   MAX_BOT_TOKEN=
   MAX_BOT_ACCESS_TOKEN=

   # === VK ===
   VK_APP_ID=
   VK_APP_SECRET=
   VK_BOT_TOKEN=
   VK_CONFIRMATION_TOKEN=

   # === Robokassa ===
   ROBOKASSA_RESULT_URL=
   ```

4. **Update .gitignore** -- add missing entries while keeping existing ones:
   ```
   __pycache__/
   *.pyc
   .env
   .env.local
   .env.production
   .venv/
   *.egg-info/
   dist/
   .mypy_cache/
   .pytest_cache/
   .ruff_cache/
   .superpowers/
   node_modules/
   build/
   .DS_Store
   docker-compose.override.yml
   ```
  </action>
  <verify>
    <automated>cd /Users/yannovak/development/projects/master_crm && grep -q "DOMAIN" Caddyfile && grep -q "nosniff" Caddyfile && grep -q "encode gzip" Caddyfile && test -f .env.production && grep -q "ROBOKASSA_RESULT_URL" .env.production && grep -q "BASE_WEBHOOK_URL" .env.production && grep -q "WEB_ADMIN_URL" .env.production && grep -q "VK_APP_ID" .env.example && grep -q "node_modules" .gitignore && grep -q "DS_Store" .gitignore && grep -q "docker-compose.override" .gitignore && echo "PASS"</automated>
  </verify>
  <done>Caddyfile uses {$DOMAIN} with automatic TLS, security headers, gzip. .env.production has all required vars with example values. .env.example matches structure with dev defaults. .gitignore covers node_modules, dist, build, .DS_Store, .env.local, .env.production, docker-compose.override.yml.</done>
</task>

<task type="auto">
  <name>Task 3: Fix master-auth localStorage persistence + phone validation</name>
  <files>frontend/src/stores/master-auth.ts, frontend/src/pages/client/BookingForm.tsx</files>
  <action>
1. **Fix frontend/src/stores/master-auth.ts** -- add localStorage persistence using the same pattern as web/src/stores/auth.ts:
   - Add `const TOKEN_KEY = "master_token";` constant
   - Add the three safe storage helpers: `safeGetItem`, `safeSetItem`, `safeRemoveItem` (identical to web/src/stores/auth.ts)
   - Add `hydrate: () => void` to the MasterAuthState interface
   - In `login` success handler: after setting state, call `safeSetItem(TOKEN_KEY, data.access_token)`
   - In `setToken`: call `safeSetItem(TOKEN_KEY, token)` when token is non-null, `safeRemoveItem(TOKEN_KEY)` when null
   - In `logout`: call `safeRemoveItem(TOKEN_KEY)` before resetting state
   - Add `hydrate` method: reads token via `safeGetItem(TOKEN_KEY)`, if exists sets `{ token, isAuthenticated: true }`
   - Leave `masterApiRequest` function unchanged

2. **Fix phone validation in frontend/src/pages/client/BookingForm.tsx**:
   - In the `validate` function, change `cleanedPhone.length < 12` to `cleanedPhone.length !== 12`
   - This ensures exactly 11 digits (the cleanPhone returns "+7XXXXXXXXXX" = 12 chars for valid Russian numbers)
   - Also cap the formatPhone function input: after normalizing digits to start with "7", truncate to max 11 digits: `phone = phone.slice(0, 11)` before formatting. This prevents users from entering more than 11 digits.
  </action>
  <verify>
    <automated>cd /Users/yannovak/development/projects/master_crm && grep -q "master_token" frontend/src/stores/master-auth.ts && grep -q "safeGetItem" frontend/src/stores/master-auth.ts && grep -q "hydrate" frontend/src/stores/master-auth.ts && grep -q "!== 12" frontend/src/pages/client/BookingForm.tsx && grep -q "slice(0, 11)" frontend/src/pages/client/BookingForm.tsx && echo "PASS"</automated>
  </verify>
  <done>Master JWT token persists in localStorage under "master_token" key, with hydrate() for reload recovery. Phone validation rejects anything that is not exactly 11 digits (+7 + 10 digits), and input is capped at 11 digits to prevent over-entry.</done>
</task>

</tasks>

<verification>
All three tasks verified individually via automated checks. Full verification:
1. `docker compose config` validates compose file syntax
2. grep checks confirm all key patterns are present in all modified files
3. No runtime tests needed -- these are config and simple code fixes
</verification>

<success_criteria>
- frontend/Dockerfile and web/Dockerfile produce nginx images (not dev servers)
- docker-compose.yml: no --reload, 4 workers, alembic auto-migration, restart:unless-stopped on all, healthchecks
- .dockerignore exists for backend, frontend, web
- Caddyfile: TLS via domain variable, security headers, gzip
- .env.production: complete template with all vars
- .env.example: updated to match structure
- .gitignore: covers node_modules, dist, build, .DS_Store, .env.local, .env.production, override
- master-auth.ts: localStorage persistence with hydrate()
- BookingForm.tsx: phone exactly 11 digits, input capped
</success_criteria>

<output>
After completion, create `.planning/quick/260318-srs-fix-all-pre-deployment-issues-for-vps-de/260318-srs-SUMMARY.md`
</output>
