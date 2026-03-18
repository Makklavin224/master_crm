---
phase: 6
slug: web-admin-panel
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest + @testing-library/react + jsdom |
| **Config file** | web/vitest.config.ts |
| **Quick run command** | `cd web && pnpm test -- --run` |
| **Full suite command** | `cd web && pnpm build && pnpm test -- --run` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pnpm build` (TypeScript check)
- **After every plan wave:** Run full suite (build + vitest)
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | WEB-01..05 | build | `pnpm build` | ❌ W0 | ⬜ pending |
| 06-01-02 | 01 | 1 | WEB-05 | build | `pnpm build` | ❌ W0 | ⬜ pending |
| 06-02-01 | 02 | 2 | WEB-01 | build+test | `pnpm build && pnpm test` | ❌ W0 | ⬜ pending |
| 06-02-02 | 02 | 2 | WEB-03 | build+test | `pnpm build && pnpm test` | ❌ W0 | ⬜ pending |
| 06-03-01 | 03 | 2 | WEB-02,04 | build+test | `pnpm build && pnpm test` | ❌ W0 | ⬜ pending |
| 06-03-02 | 03 | 2 | WEB-05 | build+test | `pnpm build && pnpm test` | ❌ W0 | ⬜ pending |

---

## Wave 0 Requirements

- [ ] `web/vitest.config.ts` — vitest setup with jsdom
- [ ] `web/src/test/setup.ts` — test setup file
- [ ] `web/src/pages/CalendarPage.test.tsx` — calendar page test stubs
- [ ] `web/src/pages/ClientsPage.test.tsx` — clients page test stubs
- [ ] `web/src/pages/ServicesPage.test.tsx` — services page test stubs
- [ ] `web/src/pages/PaymentsPage.test.tsx` — payments page test stubs
- [ ] `web/src/pages/SettingsPage.test.tsx` — settings page test stubs

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| QR code login flow | WEB-05 | Requires TG bot + real QR scanning | Generate QR in bot, scan, verify web auto-logs in |
| FullCalendar visual | WEB-01 | Visual inspection | Open /admin/calendar, verify day/week/month views render |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify
- [ ] Wave 0 covers all test stubs
- [ ] `nyquist_compliant: true` set

**Approval:** pending
