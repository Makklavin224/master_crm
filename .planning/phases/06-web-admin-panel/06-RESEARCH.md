# Phase 6: Web Admin Panel - Research

**Researched:** 2026-03-18
**Domain:** React + Ant Design desktop web panel (SPA consuming existing REST API)
**Confidence:** HIGH

## Summary

Phase 6 is a pure frontend project: a separate React SPA in `web/` that consumes the same REST API the mini-app already uses. The backend is 100% ready with all endpoints for auth, bookings, clients, services, payments, schedule, and settings. The existing mini-app (`frontend/`) already defines all TypeScript interfaces and TanStack Query hooks for the API surface -- these patterns should be mirrored (not shared, since the apps use different UI frameworks).

The recommended stack is **Ant Design 5.x** (not v6) with the built-in `Layout.Sider` + `Menu` for sidebar navigation, **FullCalendar 6.x** for calendar/schedule view, and the same data layer pattern (TanStack Query + Zustand) from the mini-app. Ant Design v6 exists but `@ant-design/pro-components` only has a beta release for v6 compatibility; using antd 5.29.3 (latest stable in the 5.x line) avoids ecosystem friction.

**Primary recommendation:** Use antd 5.29.3 with Layout.Sider (not ProLayout), FullCalendar 6.1.20 for schedule views, and mirror the existing `frontend/src/api/` TanStack Query hook patterns exactly. Auth store uses Zustand with localStorage persistence for JWT. Three login methods (email/password form, QR poll, magic link redirect) all resolve to the same JWT token stored in localStorage.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Sidebar + content layout (Ant Design ProLayout or Layout.Sider)
- Left sidebar with menu: Kalendar, Klienty, Uslugi, Platezhi, Nastroyki
- Main content area on the right
- Collapsible sidebar for smaller screens
- Light theme by default + dark theme toggle
- Uses Ant Design theme system (ConfigProvider)
- Accent color: #6C5CE7 (same as mini-app for brand consistency)
- All three auth methods: email+password, QR code scan, magic link
- JWT token stored in localStorage, same API endpoints as mini-app
- Pages: Dashboard/Calendar, Clients, Services, Payments, Settings
- web/ directory in monorepo (alongside backend/ and frontend/)
- Own package.json, Vite config, Docker service
- Shares nothing with frontend/ mini-app
- Served by Caddy at /admin/ path

### Claude's Discretion
- Ant Design version and specific components
- Table column configurations
- Calendar component choice (FullCalendar, Ant Calendar, or custom)
- QR code generation for login (frontend or backend)
- Magic link token generation and validation
- Responsive breakpoints
- Data fetching patterns (TanStack Query same as mini-app, or SWR)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| WEB-01 | Web panel -- calendar and booking list (day/week view) | FullCalendar 6.x with timeGrid + dayGrid plugins; existing `/bookings` API with date_from/date_to filters |
| WEB-02 | Web panel -- client management (list, visit history) | Ant Design Table with search; existing `/clients` and `/clients/:id` API endpoints |
| WEB-03 | Web panel -- service CRUD (create, edit, delete, categories) | Ant Design Table + Modal forms; existing `/services` CRUD endpoints |
| WEB-04 | Web panel -- payment history and receipt statuses | Ant Design Table with filters + status tags; existing `/payments/history` with filter params |
| WEB-05 | Web panel -- schedule settings and master profile | Ant Design Form components; existing `/schedule`, `/settings`, `/settings/notifications`, `/settings/payment` endpoints |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| antd | 5.29.3 | UI component library | Stable v5 line; ProLayout/ProComponents fully compatible; v6 ecosystem still maturing |
| @ant-design/icons | 5.6.1 | Icon library | Must match antd major version; 5.x for antd 5.x |
| react | ^19.2.4 | UI framework | Same version as mini-app |
| react-dom | ^19.2.4 | DOM renderer | Same version as mini-app |
| react-router-dom | ^7.13.1 | Client-side routing | Same version as mini-app |
| @tanstack/react-query | ^5.91.0 | Data fetching/caching | Same pattern as mini-app; proven in this project |
| zustand | ^5.0.12 | Auth state management | Same pattern as mini-app auth store |
| dayjs | ^1.11.20 | Date manipulation | Same as mini-app; Ant Design uses dayjs internally |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @fullcalendar/react | 6.1.20 | Calendar component | WEB-01: schedule view with time blocks |
| @fullcalendar/daygrid | 6.1.20 | Month/day grid view | Month overview of bookings |
| @fullcalendar/timegrid | 6.1.20 | Time-slot week/day view | Day/week schedule with time blocks |
| @fullcalendar/interaction | 6.1.20 | Click/drag on calendar | Creating bookings by clicking time slots |
| qrcode.react | 4.2.0 | QR code rendering | Login page: display QR for bot scan |
| vite | ^8.0.0 | Build tool | Same as mini-app |
| @vitejs/plugin-react | ^6.0.1 | React fast refresh | Same as mini-app |
| typescript | ~5.9.3 | Type checking | Same as mini-app |

### Testing
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| vitest | ^4.1.0 | Test runner | Unit/integration tests |
| @testing-library/react | ^16.3.2 | Component testing | Testing React components |
| @testing-library/jest-dom | ^6.9.1 | DOM assertions | Custom matchers |
| jsdom | ^29.0.0 | Browser environment | Test environment |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| antd 5.29.3 | antd 6.3.3 | v6 is newer but ProComponents beta-only; v5 is battle-tested with full ProLayout support if needed |
| @ant-design/pro-layout | Layout.Sider + Menu | ProLayout adds umi dependency complexity; built-in Layout is simpler and sufficient for this sidebar |
| FullCalendar | Ant Design Calendar | Ant Calendar is date-picker oriented, lacks timeGrid/week view with time blocks; FullCalendar is purpose-built |
| TanStack Query | SWR | TanStack Query already proven in mini-app, more features (mutation support, query invalidation) |
| qrcode.react | react-qr-code | qrcode.react is more popular (4.2M weekly downloads), supports SVG and Canvas rendering |

**Installation:**
```bash
cd web
pnpm add antd @ant-design/icons react react-dom react-router-dom @tanstack/react-query zustand dayjs @fullcalendar/react @fullcalendar/daygrid @fullcalendar/timegrid @fullcalendar/interaction qrcode.react
pnpm add -D vite @vitejs/plugin-react typescript @types/react @types/react-dom vitest @testing-library/react @testing-library/jest-dom jsdom eslint @eslint/js typescript-eslint eslint-plugin-react-hooks eslint-plugin-react-refresh globals
```

## Architecture Patterns

### Recommended Project Structure
```
web/
├── index.html
├── package.json
├── pnpm-lock.yaml
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── vite.config.ts
├── Dockerfile
├── public/
│   └── favicon.svg
└── src/
    ├── main.tsx              # Entry point
    ├── App.tsx               # Router + providers
    ├── theme.ts              # Ant Design theme tokens (light + dark)
    ├── api/
    │   ├── client.ts         # Base API client (fetch + Bearer token)
    │   ├── bookings.ts       # Booking queries/mutations
    │   ├── clients.ts        # Client queries
    │   ├── services.ts       # Service CRUD
    │   ├── payments.ts       # Payment queries
    │   ├── schedule.ts       # Schedule queries/mutations
    │   └── settings.ts       # Settings queries/mutations
    ├── stores/
    │   ├── auth.ts           # Zustand: JWT + login/logout + localStorage
    │   └── theme.ts          # Zustand: light/dark preference + localStorage
    ├── layouts/
    │   └── AdminLayout.tsx   # Layout.Sider + Menu + Content + theme toggle
    ├── pages/
    │   ├── LoginPage.tsx     # Email/pass + QR + magic link tabs
    │   ├── CalendarPage.tsx  # FullCalendar schedule view
    │   ├── ClientsPage.tsx   # Table + search
    │   ├── ClientDetailPage.tsx
    │   ├── ServicesPage.tsx  # CRUD table + modal
    │   ├── PaymentsPage.tsx  # History table + filters
    │   └── SettingsPage.tsx  # Schedule + notifications + payment + profile
    └── components/
        ├── BookingDrawer.tsx  # Side drawer for booking details
        ├── ServiceModal.tsx   # Create/edit service modal
        └── StatusTag.tsx      # Reusable booking/payment status tags
```

### Pattern 1: API Client with Auth Store (mirror mini-app)
**What:** Zustand store manages JWT token; API client reads token from store and attaches Bearer header. localStorage persists token across page reloads.
**When to use:** Every authenticated API call.
**Example:**
```typescript
// stores/auth.ts
import { create } from 'zustand';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const TOKEN_KEY = 'admin_token';

interface AuthState {
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  loginEmail: (email: string, password: string) => Promise<boolean>;
  setToken: (token: string) => void;
  logout: () => void;
  hydrate: () => void;
}

export const useAuth = create<AuthState>((set) => ({
  token: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  loginEmail: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Login failed' }));
        set({ isLoading: false, error: err.detail });
        return false;
      }
      const { access_token } = await res.json();
      localStorage.setItem(TOKEN_KEY, access_token);
      set({ token: access_token, isAuthenticated: true, isLoading: false });
      return true;
    } catch {
      set({ isLoading: false, error: 'Network error' });
      return false;
    }
  },

  setToken: (token) => {
    localStorage.setItem(TOKEN_KEY, token);
    set({ token, isAuthenticated: true, error: null });
  },

  logout: () => {
    localStorage.removeItem(TOKEN_KEY);
    set({ token: null, isAuthenticated: false });
  },

  hydrate: () => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) set({ token, isAuthenticated: true });
  },
}));

// api/client.ts
import { useAuth } from '../stores/auth';

export class ApiError extends Error {
  status: number;
  detail: string;
  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const { token } = useAuth.getState();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Network error' }));
    if (res.status === 401) {
      useAuth.getState().logout();
    }
    throw new ApiError(res.status, err.detail || `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}
```

### Pattern 2: Theme Toggle with ConfigProvider
**What:** Zustand store for dark/light preference; ConfigProvider wraps app with `algorithm` prop.
**When to use:** App root level.
**Example:**
```typescript
// stores/theme.ts
import { create } from 'zustand';

interface ThemeState {
  isDark: boolean;
  toggle: () => void;
}

export const useThemeStore = create<ThemeState>((set) => ({
  isDark: localStorage.getItem('admin_theme') === 'dark',
  toggle: () =>
    set((s) => {
      const next = !s.isDark;
      localStorage.setItem('admin_theme', next ? 'dark' : 'light');
      return { isDark: next };
    }),
}));

// theme.ts
import { ThemeConfig, theme } from 'antd';

export const lightTheme: ThemeConfig = {
  algorithm: theme.defaultAlgorithm,
  token: {
    colorPrimary: '#6C5CE7',
    borderRadius: 8,
    fontFamily: "'Inter', -apple-system, sans-serif",
  },
};

export const darkTheme: ThemeConfig = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: '#6C5CE7',
    borderRadius: 8,
    fontFamily: "'Inter', -apple-system, sans-serif",
  },
};

// App.tsx (root)
import { ConfigProvider } from 'antd';
import { useThemeStore } from './stores/theme';
import { lightTheme, darkTheme } from './theme';

function App() {
  const isDark = useThemeStore((s) => s.isDark);
  return (
    <ConfigProvider theme={isDark ? darkTheme : lightTheme}>
      {/* ... */}
    </ConfigProvider>
  );
}
```

### Pattern 3: Admin Layout with Sidebar
**What:** Ant Design Layout + Layout.Sider + Menu with react-router-dom navigation.
**When to use:** Wraps all authenticated pages.
**Example:**
```typescript
// layouts/AdminLayout.tsx
import { Layout, Menu, Button, Switch } from 'antd';
import {
  CalendarOutlined,
  TeamOutlined,
  AppstoreOutlined,
  DollarOutlined,
  SettingOutlined,
  LogoutOutlined,
  BulbOutlined,
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useState } from 'react';
import { useAuth } from '../stores/auth';
import { useThemeStore } from '../stores/theme';

const { Sider, Content, Header } = Layout;

const menuItems = [
  { key: '/calendar', icon: <CalendarOutlined />, label: 'Kalendar' },
  { key: '/clients', icon: <TeamOutlined />, label: 'Klienty' },
  { key: '/services', icon: <AppstoreOutlined />, label: 'Uslugi' },
  { key: '/payments', icon: <DollarOutlined />, label: 'Platezhi' },
  { key: '/settings', icon: <SettingOutlined />, label: 'Nastroyki' },
];

export function AdminLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const logout = useAuth((s) => s.logout);
  const { isDark, toggle } = useThemeStore();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        breakpoint="lg"
        theme={isDark ? 'dark' : 'light'}
      >
        <div style={{ padding: 16, textAlign: 'center', fontWeight: 700 }}>
          {collapsed ? 'M' : 'MasterCRM'}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: '0 24px', display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 16 }}>
          <Switch
            checked={isDark}
            onChange={toggle}
            checkedChildren={<BulbOutlined />}
            unCheckedChildren={<BulbOutlined />}
          />
          <Button type="text" icon={<LogoutOutlined />} onClick={logout} />
        </Header>
        <Content style={{ margin: 24 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
```

### Pattern 4: QR Code Login Flow
**What:** Backend generates a one-time auth token, frontend renders it as QR, polls for completion.
**When to use:** LoginPage QR tab.
**Flow:**
1. Web panel calls `POST /api/v1/auth/qr/init` -- backend creates a pending QR session (UUID + short-lived token), returns `{ session_id, qr_payload }`.
2. Frontend renders `qr_payload` as QR code using `qrcode.react`.
3. `qr_payload` is a deep link to the bot: `https://t.me/MasterCRMBot?start=qr_{session_id}`.
4. User scans QR in Telegram, bot receives `/start qr_{session_id}`, bot calls `POST /api/v1/auth/qr/confirm` with session_id + tg_user_id.
5. Frontend polls `GET /api/v1/auth/qr/status/{session_id}` every 3 seconds.
6. Once confirmed, status endpoint returns `{ status: 'confirmed', access_token: '...' }`.
7. Frontend stores token in auth store, navigates to dashboard.

**NOTE:** This requires 3 new backend endpoints (init, confirm, status). The CONTEXT.md says "backend API 100% ready -- no new endpoints" but QR and magic link auth flows were not part of the existing API. These endpoints are minimal (create/read/update a session record) and should be added as part of this phase.

### Pattern 5: Magic Link Login Flow
**What:** User requests magic link via bot, bot sends one-time URL, clicking opens web panel with token.
**When to use:** LoginPage magic link tab.
**Flow:**
1. Web panel shows instructions: "Send /login to @MasterCRMBot".
2. User sends `/login` to bot. Bot generates a one-time token (UUID, expires in 10 minutes), stores it in DB.
3. Bot sends back: "Click to login: https://example.com/admin/auth/magic?token={UUID}".
4. User clicks link. Web panel `/auth/magic` route extracts token from URL.
5. Frontend calls `POST /api/v1/auth/magic/verify` with `{ token }`.
6. Backend validates token (exists, not expired, not used), marks as used, returns `{ access_token }`.
7. Frontend stores JWT, navigates to dashboard.

**NOTE:** Requires 1 new backend endpoint (verify) + bot command handler. Same caveat as QR: minimal backend additions needed.

### Anti-Patterns to Avoid
- **Sharing code between `frontend/` and `web/`:** These are separate apps with different UI frameworks (Tailwind vs Ant Design). Copy the API interface types, do not import across projects.
- **Using ProLayout without umi:** ProLayout expects umi's route injection. Without it, manual route/location props are needed, adding complexity for minimal gain over Layout.Sider.
- **Using Ant Design Calendar for schedule:** The built-in Calendar component is a date picker, not a schedule viewer. It cannot display time blocks or week views with hourly slots.
- **Storing JWT in cookies:** The mini-app uses localStorage. Keep consistent. The web panel runs on the same domain, so CORS is not an issue.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Calendar/schedule view | Custom time grid with CSS | FullCalendar 6.x | Time zones, drag-drop, event overlap, responsive sizing -- hundreds of edge cases |
| Data tables with sort/filter | Custom table components | Ant Design Table | Built-in sort, filter, pagination, loading states, empty states |
| Form validation | Custom validation logic | Ant Design Form with rules | Async validation, field dependencies, error display all built-in |
| Dark/light theming | CSS class toggling | ConfigProvider algorithm | Token system cascades to all components automatically |
| QR code rendering | Canvas drawing | qrcode.react | Error correction levels, sizing, SVG/Canvas output |
| Date formatting | Manual string manipulation | dayjs | Locale support, relative time, timezone handling |
| Data fetching/caching | Custom fetch + state | TanStack Query | Cache invalidation, refetch on focus, optimistic updates, deduplication |

**Key insight:** Ant Design provides 60+ components covering tables, forms, modals, drawers, dropdowns, tags, badges, and more. The web panel should use these components directly, avoiding custom CSS or hand-rolled UI for standard patterns.

## Common Pitfalls

### Pitfall 1: Ant Design CSS-in-JS bundle size
**What goes wrong:** Importing all of antd bloats the bundle.
**Why it happens:** Tree-shaking works with named imports but CSS-in-JS styles are generated at runtime.
**How to avoid:** Use named imports: `import { Button, Table } from 'antd'` (not `import antd from 'antd'`). Ant Design 5.x tree-shakes correctly with named imports.
**Warning signs:** Bundle size > 500KB gzipped for initial load.

### Pitfall 2: FullCalendar CSS not loading
**What goes wrong:** Calendar renders but has no styling -- events overlap, grid invisible.
**Why it happens:** FullCalendar 6.x bundles its own CSS but some bundler configs strip it.
**How to avoid:** Ensure Vite handles CSS from node_modules. FullCalendar 6 uses CSS imports internally that Vite handles by default -- no manual CSS import needed.
**Warning signs:** Calendar visible but unstyled, events stacking vertically.

### Pitfall 3: Price display in rubles vs kopecks
**What goes wrong:** Prices show as 100000 instead of 1000.00.
**Why it happens:** Backend stores prices in kopecks (integer) to avoid float precision issues (established project decision).
**How to avoid:** Always divide by 100 for display: `(price / 100).toLocaleString('ru-RU', { minimumFractionDigits: 0 })`. Create a shared `formatPrice` utility.
**Warning signs:** Prices appearing 100x too large.

### Pitfall 4: JWT expiration without refresh
**What goes wrong:** User works for hours, then all requests fail with 401.
**Why it happens:** JWT expires (backend default), no refresh token mechanism exists.
**How to avoid:** In the API client, intercept 401 responses and redirect to login page. Call `useAuth.getState().logout()` on 401. Optionally show a "Session expired" notification.
**Warning signs:** 401 errors after extended use.

### Pitfall 5: Vite base path misconfiguration
**What goes wrong:** Assets load from `/` instead of `/admin/`, causing 404s in production.
**Why it happens:** Caddy serves web panel at `/admin/`, but Vite defaults to `/` base.
**How to avoid:** Set `base: '/admin/'` in vite.config.ts. React Router needs `<BrowserRouter basename="/admin">`.
**Warning signs:** Works in dev but blank page in production, CSS/JS 404s.

### Pitfall 6: FullCalendar event timezone mismatch
**What goes wrong:** Bookings appear at wrong times.
**Why it happens:** Backend returns ISO timestamps in master's timezone, FullCalendar renders in browser timezone.
**How to avoid:** Use FullCalendar's `timeZone` prop set to master's timezone (from `/auth/me` or `/settings`). All `starts_at`/`ends_at` from the API are already in master's local timezone.
**Warning signs:** Bookings shifted by several hours.

### Pitfall 7: Docker pnpm corepack
**What goes wrong:** Docker build fails with "pnpm: command not found".
**Why it happens:** Node 20 image includes corepack but it is not enabled by default.
**How to avoid:** Add `RUN corepack enable` in Dockerfile before `pnpm install` (same pattern as existing frontend Dockerfile).
**Warning signs:** Build failure in CI/Docker.

## Code Examples

### FullCalendar Schedule View (WEB-01)
```typescript
// pages/CalendarPage.tsx
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import { useBookings } from '../api/bookings';
import { useMemo, useState } from 'react';
import { Card, Segmented } from 'antd';

// Map booking status to calendar event color
const STATUS_COLORS: Record<string, string> = {
  confirmed: '#6C5CE7',
  pending: '#FDCB6E',
  completed: '#00B894',
  cancelled: '#D63031',
};

export function CalendarPage() {
  const [dateRange, setDateRange] = useState({
    date_from: '', date_to: ''
  });
  const { data } = useBookings(dateRange);

  const events = useMemo(() =>
    (data?.items ?? []).map((b) => ({
      id: b.id,
      title: `${b.service_name} - ${b.client_name}`,
      start: b.starts_at,
      end: b.ends_at,
      backgroundColor: STATUS_COLORS[b.status] || '#6C5CE7',
      borderColor: 'transparent',
      extendedProps: { booking: b },
    })),
    [data],
  );

  return (
    <Card>
      <FullCalendar
        plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
        initialView="timeGridWeek"
        headerToolbar={{
          left: 'prev,next today',
          center: 'title',
          right: 'timeGridDay,timeGridWeek,dayGridMonth',
        }}
        locale="ru"
        firstDay={1}
        slotMinTime="08:00:00"
        slotMaxTime="22:00:00"
        allDaySlot={false}
        events={events}
        datesSet={(info) => {
          setDateRange({
            date_from: info.startStr.split('T')[0],
            date_to: info.endStr.split('T')[0],
          });
        }}
        eventClick={(info) => {
          // Open booking detail drawer
        }}
      />
    </Card>
  );
}
```

### Clients Table with Search (WEB-02)
```typescript
// pages/ClientsPage.tsx
import { Table, Input, Card } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { useClients } from '../api/clients';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';

export function ClientsPage() {
  const { data, isLoading } = useClients();
  const [search, setSearch] = useState('');
  const navigate = useNavigate();

  const filtered = (data ?? []).filter((c) =>
    c.client.name.toLowerCase().includes(search.toLowerCase()) ||
    c.client.phone.includes(search)
  );

  const columns = [
    { title: 'Imya', dataIndex: ['client', 'name'], sorter: (a: any, b: any) => a.client.name.localeCompare(b.client.name) },
    { title: 'Telefon', dataIndex: ['client', 'phone'] },
    { title: 'Vizity', dataIndex: 'visit_count', sorter: (a: any, b: any) => a.visit_count - b.visit_count },
    { title: 'Posledniy vizit', dataIndex: 'last_visit_at', render: (v: string) => dayjs(v).format('DD.MM.YYYY') },
  ];

  return (
    <Card title="Klienty">
      <Input
        prefix={<SearchOutlined />}
        placeholder="Poisk po imeni ili telefonu"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        style={{ marginBottom: 16, maxWidth: 400 }}
      />
      <Table
        columns={columns}
        dataSource={filtered}
        rowKey={(r) => r.client.id}
        loading={isLoading}
        onRow={(record) => ({
          onClick: () => navigate(`/clients/${record.client.id}`),
          style: { cursor: 'pointer' },
        })}
        pagination={{ pageSize: 20 }}
      />
    </Card>
  );
}
```

### Service CRUD with Modal (WEB-03)
```typescript
// Key pattern: Ant Design Table + Modal form for CRUD
// Table shows services with edit/delete actions
// Modal with Form for create/edit
// useMutation with queryClient.invalidateQueries on success

import { Table, Button, Modal, Form, Input, InputNumber, Space, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useServices, useCreateService, useUpdateService, useDeleteService } from '../api/services';

// Form fields match ServiceCreate/ServiceUpdate interfaces from backend:
// name (string), description (string|null), duration_minutes (number), price (number in kopecks), category (string|null)
```

### Vite Config for /admin/ Base Path
```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: '/admin/',
  server: { host: '0.0.0.0', port: 3001 },
  build: { outDir: 'dist' },
});
```

### Docker Service for Web Panel
```yaml
# Addition to docker-compose.yml
web:
  build:
    context: ./web
    dockerfile: Dockerfile
  volumes:
    - ./web:/app
    - /app/node_modules
  ports:
    - "3001:3001"
  command: pnpm dev --host 0.0.0.0 --port 3001
```

### Caddy Route Addition
```
# Addition to Caddyfile
handle /admin/* {
    uri strip_prefix /admin
    reverse_proxy web:3001
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| antd 4.x with Less theming | antd 5.x with CSS-in-JS + ConfigProvider tokens | Nov 2022 (v5.0) | No more Less overrides, runtime theme switching |
| ProLayout required for sidebar | Layout.Sider + Menu sufficient | antd 5.x | ProLayout adds umi dependency, built-in Layout is simpler |
| FullCalendar 5 with @fullcalendar/common | FullCalendar 6 (no @fullcalendar/common) | 2023 | Simplified package structure |
| Create React App | Vite | 2023+ | CRA is deprecated, Vite is the standard |
| react-router-dom v5 | v7.x | 2024-2025 | Data router, loader/action patterns available (optional) |

**Deprecated/outdated:**
- antd 4.x: Less-based theming, no ConfigProvider token system
- `@fullcalendar/common`: Removed in v6, functionality merged into `@fullcalendar/core`
- Create React App: No longer maintained, Vite is the replacement
- `@ant-design/pro-layout` as standalone: Prefer built-in Layout.Sider for non-umi projects

## Open Questions

1. **QR + Magic Link Backend Endpoints**
   - What we know: The existing backend has email/password login (`POST /auth/login`) and messenger auth endpoints (`POST /auth/tg`, `/auth/max`, `/auth/vk`). QR and magic link are new auth flows.
   - What's unclear: Whether CONTEXT.md's "backend API 100% ready" means these endpoints exist or need to be created.
   - Recommendation: Plan for creating 3-4 minimal backend endpoints (QR init/status/confirm, magic link verify) as part of this phase. They are small (single DB table for auth sessions) and follow existing patterns.

2. **Master Profile Data on /auth/me**
   - What we know: `GET /auth/me` returns `MasterRead` schema (name, email, etc.).
   - What's unclear: Whether it includes the master's timezone (needed for FullCalendar `timeZone` prop).
   - Recommendation: Check `MasterRead` schema. If timezone is missing, it may need to be added.

3. **Russian Locale for FullCalendar**
   - What we know: FullCalendar supports locales via `locale` prop.
   - What's unclear: Whether `@fullcalendar/core/locales/ru` needs explicit import or works with string `"ru"`.
   - Recommendation: Import `ruLocale from '@fullcalendar/core/locales/ru'` and pass as `locales={[ruLocale]}` prop.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 4.1.0 + @testing-library/react 16.3.2 |
| Config file | `web/vitest.config.ts` (none yet -- Wave 0) |
| Quick run command | `cd web && pnpm test` |
| Full suite command | `cd web && pnpm test -- --run` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| WEB-01 | Calendar renders bookings from API | unit | `cd web && pnpm vitest run src/pages/CalendarPage.test.tsx -t "renders" --reporter=verbose` | Wave 0 |
| WEB-02 | Clients table filters by search | unit | `cd web && pnpm vitest run src/pages/ClientsPage.test.tsx -t "search" --reporter=verbose` | Wave 0 |
| WEB-03 | Service CRUD: create, edit, delete | unit | `cd web && pnpm vitest run src/pages/ServicesPage.test.tsx --reporter=verbose` | Wave 0 |
| WEB-04 | Payment table shows filtered history | unit | `cd web && pnpm vitest run src/pages/PaymentsPage.test.tsx --reporter=verbose` | Wave 0 |
| WEB-05 | Settings form saves schedule config | unit | `cd web && pnpm vitest run src/pages/SettingsPage.test.tsx --reporter=verbose` | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd web && pnpm vitest run --reporter=verbose`
- **Per wave merge:** `cd web && pnpm vitest run --reporter=verbose`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `web/vitest.config.ts` -- Vitest config with jsdom environment
- [ ] `web/src/test/setup.ts` -- Testing library setup (jest-dom matchers)
- [ ] `web/src/pages/CalendarPage.test.tsx` -- covers WEB-01
- [ ] `web/src/pages/ClientsPage.test.tsx` -- covers WEB-02
- [ ] `web/src/pages/ServicesPage.test.tsx` -- covers WEB-03
- [ ] `web/src/pages/PaymentsPage.test.tsx` -- covers WEB-04
- [ ] `web/src/pages/SettingsPage.test.tsx` -- covers WEB-05
- [ ] Framework install: `cd web && pnpm add -D vitest @testing-library/react @testing-library/jest-dom jsdom`

## Sources

### Primary (HIGH confidence)
- npm registry -- verified all package versions via `npm view [pkg] version` (2026-03-18)
- Existing codebase: `frontend/src/api/` -- all API interfaces and TanStack Query patterns
- Existing codebase: `backend/app/api/v1/auth.py` -- existing auth endpoints (register, login, tg, max, vk)
- Existing codebase: `frontend/src/stores/master-auth.ts` -- JWT auth store pattern with Zustand
- Existing codebase: `docker-compose.yml`, `Caddyfile`, `frontend/Dockerfile` -- infrastructure patterns

### Secondary (MEDIUM confidence)
- [Ant Design theme customization](https://ant.design/docs/react/customize-theme/) -- ConfigProvider, algorithm, token system
- [Ant Design Layout components](https://ant.design/components/layout/) -- Layout.Sider, collapsible, breakpoint
- [FullCalendar React docs](https://fullcalendar.io/docs/react) -- installation, plugin system, props
- [FullCalendar TimeGrid docs](https://fullcalendar.io/docs/timegrid-view) -- timeGridWeek/Day configuration
- [Ant Design v5 to v6 migration](https://ant.design/docs/react/migration-v6/) -- breaking changes assessment
- [Pro-components antd v6 compatibility](https://github.com/ant-design/pro-components/issues/9099) -- beta status confirmed

### Tertiary (LOW confidence)
- QR login flow pattern -- synthesized from multiple sources (IBM Verify docs, Medium article, OAuth device flow docs); specific backend implementation needs validation
- Magic link flow -- synthesized from multiple tutorials; specific endpoint design needs validation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all versions verified via npm registry, patterns proven in existing mini-app
- Architecture: HIGH -- mirrors existing frontend/ structure with Ant Design instead of Tailwind
- Calendar: HIGH -- FullCalendar is the de facto React calendar library; verified v6.1.20 packages
- Auth flows (email): HIGH -- endpoint already exists (`POST /auth/login`)
- Auth flows (QR/magic): MEDIUM -- flow patterns are standard but require new backend endpoints
- Pitfalls: HIGH -- derived from real project context (kopecks, timezone, base path)
- Theming: HIGH -- Ant Design ConfigProvider algorithm approach verified in official docs

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (stable ecosystem, antd 5.x LTS)
