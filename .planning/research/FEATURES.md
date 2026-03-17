# Feature Landscape

**Domain:** Multi-messenger CRM with booking & auto-tax receipts for self-employed professionals (Russia)
**Researched:** 2026-03-17
**Overall Confidence:** HIGH (based on competitor analysis of YCLIENTS, DIKIDI, EasyWeek, Okoshki, Beauty-Bot, samoCRM, Master CRM, Salebot, Prodamus, and various Telegram bots)

## Competitive Context

The Russian market for self-employed booking/CRM tools is fragmented across three tiers:

1. **Enterprise-grade** (YCLIENTS 686+/mo, DIKIDI 450+/mo, EasyWeek) -- full-featured salon management: scheduling, inventory, payroll, loyalty, analytics, multi-location. Overkill and expensive for solo masters.
2. **Lightweight schedulers** (Okoshki 490/mo, "ZapishiMenya" 390/mo, Beauty-Bot 990+/mo, Mira) -- Telegram bots / mini-apps focused on appointment booking. No payments, no tax integration, no multi-messenger.
3. **Accounting-only** (samoCRM, Master CRM) -- income tracking and "Moy Nalog" integration. No booking, no client-facing interface.

**Critical gap nobody fills:** Booking + SBP payment + automatic "Moy Nalog" receipt + multi-messenger (TG + MAX + VK) in one product. This is the product's primary opportunity.

---

## Table Stakes

Features users expect. Missing = product feels incomplete and users leave for DIKIDI/YCLIENTS.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Service catalog** (name, duration, price) | Every competitor has this. Masters need to list what they offer. | Low | Allow categories, variable pricing (e.g., "short hair" vs "long hair"). YCLIENTS recently added multiple price variants per service. |
| **Calendar / schedule view** | Core interaction for master. Must see day/week view of all bookings at a glance. | Medium | Real-time updates critical. DIKIDI's #1 praised feature is "schedule updated in real-time". |
| **Working hours & days off** | Without this, clients cannot self-book into valid slots. | Low | Per-day granularity (not just Mon-Fri pattern). Support holidays, lunch breaks. |
| **Online self-booking by clients** | 75% of clients book online; 40% book after hours (industry stat). This is table stakes since 2020. | Medium | Must calculate available slots from: working hours - existing bookings - buffer time. Show only free slots. |
| **Client database (auto-populated)** | Every CRM competitor builds client profiles from bookings. Masters expect phone + name + visit history. | Low | Auto-fill from booking data. Phone as primary identifier (per PROJECT.md constraint). |
| **Booking confirmations** | Client must know their booking was accepted. Universal across all competitors. | Low | In-messenger notification via bot. Instant. |
| **Automated reminders** (24h + 2h) | Reduces no-shows by 30-50% (industry consensus). DIKIDI, YCLIENTS, Okoshki, all do this. | Low | Via messenger bot (free), not SMS (paid). Competitive advantage over YCLIENTS which charges for SMS. |
| **Booking management** (reschedule, cancel) | Clients expect self-service. Every competitor offers this. | Medium | Client-initiated cancel/reschedule with configurable cutoff (e.g., no cancel <2h before). Master override always available. |
| **Push/in-app notifications for master** | Master must know immediately when a new booking or cancellation happens. | Low | Messenger bot notification to master's chat. |
| **Client visit history** | Masters need to see "last visited 3 weeks ago, got haircut + coloring". Table stakes in every CRM. | Low | Auto-built from completed bookings. |
| **Basic mobile access for master** | Masters work on their feet. Phone-first management is expected. DIKIDI Business mobile app is their most popular feature. | Medium | Mini-app in messenger solves this without requiring a separate native app download. |

---

## Differentiators

Features that set the product apart. Not universally expected, but create competitive moat.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Auto tax receipt via Robokassa Robochecks** | KILLER FEATURE. No competitor in the booking space does this. samoCRM does tax but has no booking. YCLIENTS/DIKIDI require manual "Moy Nalog" receipt creation. Saves master 5-10 min per client per day. | Medium | Robokassa Robochecks SMZ is free, officially partnered with FNS. Integration: payment callback triggers receipt. Master presses "Complete" -> client gets SBP link -> payment -> auto-receipt. 3 steps instead of 9. |
| **Multi-messenger presence** (TG + MAX + VK) | No competitor exists in all three. MAX has 100M users and <5 CRM bots. First mover advantage. Clients book where they already are instead of downloading a separate app or visiting a website. | High | Single React codebase for mini-apps reduces cost. Each messenger has its own bot for notifications. MAX opening business platform spring 2026 creates a time-sensitive window. |
| **SBP payment link after service** | Master taps "Complete" -> client gets payment link in chat. No cash handling, no card terminals. Robokassa handles SBP at 2.9-3.5% commission. | Medium | Competitors either require external payment setup (YCLIENTS + YuKassa manual config) or don't have payments at all (Okoshki, Beauty-Bot). |
| **Client identification by phone across messengers** | Client books via TG, later uses VK -- recognized as same person. Unified profile. MAX provides phone automatically; TG/VK request on first booking. | Medium | Unique to multi-messenger approach. No competitor even attempts cross-messenger identity. |
| **Zero-download client experience** | Client clicks link in messenger -> mini-app opens -> books. No app store, no registration, no login. Frictionless. | Low (architectural) | Major advantage over YCLIENTS/DIKIDI which require clients to create accounts or download apps. Messenger context provides identity. |
| **Free reminders via messenger** | YCLIENTS charges extra for SMS reminders. Messenger-based reminders are free and have higher open rates (80%+ vs 20% for SMS). | Low | Cost advantage for masters AND better delivery. Significant differentiator. |
| **Web admin panel for master** | Full desktop management: schedule, clients, services, payments, analytics. Mobile mini-app for quick actions; web panel for detailed management. | High | Okoshki and lightweight bots lack this. YCLIENTS/DIKIDI have it but at 2-5x the price. |

---

## Anti-Features

Features to explicitly NOT build. Either overkill for solo masters, or actively harmful to product focus.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Inventory / stock management** | Solo masters don't track nail polish bottles in a database. YCLIENTS has this for salons; it's bloat for a solo product. 15M self-employed target != salon chains. | Nothing. Out of scope permanently. |
| **Payroll / salary calculation** | Solo masters have no employees. This is YCLIENTS territory for multi-staff salons. Adding it dilutes the product message. | Nothing. If user has employees, they should use YCLIENTS. |
| **Multi-branch management** | Solo-focused product. Branch management adds complexity that makes the product harder for the core user. | Support one "location" (or home visits as location). |
| **Loyalty programs** (points, cashback, tiers) | Complex to build, complex to explain to masters, low usage among solo professionals. DIKIDI has it and reviews say most solo masters don't use it. | Defer to v2+ if validated by user demand. In v1, simple "10th visit free" manual tracking at most. |
| **Telephony / IP phone integration** | Messengers replace phone calls for the target audience. DIKIDI integrates with UIS telephony; solo masters don't use it. | Messenger chat IS the communication channel. |
| **Native mobile app** (iOS/Android) | Mini-apps in 3 messengers already provide mobile access. A native app competes with the mini-app, fragments the experience, and costs 3-6 months of development. | Mini-app in messenger = native-quality UX without app store friction. |
| **Marketplace / client discovery** | DIKIDI has a client-facing marketplace where users find masters. Building a two-sided marketplace is a completely different business. Requires critical mass on both sides. | Masters share their booking link themselves. Viral loop: 1 master -> 40 clients -> their masters see the product. |
| **Complex analytics dashboards** | Solo masters need "how much did I earn this month?" not "conversion funnel analysis". Overbuilding analytics wastes time and confuses users. | v1: Revenue per period (day/week/month), booking count, repeat client rate. That's it. |
| **Email marketing / mass campaigns** | Solo masters don't send email newsletters. Their clients are in messengers. | Messenger broadcasts for announcements (new service, holiday schedule). |
| **Online reviews / ratings system** | Requires critical mass, moderation, fake review prevention. Different product entirely. | Let clients leave reviews on Yandex Maps / 2GIS where they already look. |
| **AI chatbot for client interaction** | Premature sophistication. Clients need to pick time + service, not chat with AI. Bot tree navigation is faster and more predictable. | Simple bot flow: Choose service -> Choose date -> Choose time -> Confirm. |

---

## Feature Dependencies

```
Service Catalog --> Online Booking (booking requires services to exist)
Working Hours --> Online Booking (slot calculation needs schedule)
Online Booking --> Client Database (auto-populated from bookings)
Online Booking --> Booking Confirmations
Online Booking --> Automated Reminders
Online Booking --> Booking Management (reschedule/cancel)
Client Database --> Visit History
SBP Payment Link --> Auto Tax Receipt (receipt triggered by payment callback)
Online Booking --> SBP Payment Link (payment happens after booking is completed)
Multi-messenger Bots --> Automated Reminders (reminders sent via bot)
Multi-messenger Bots --> Zero-download Client Experience
Phone-based Identity --> Cross-messenger Client Recognition
Web Admin Panel --> (independent, but needs same backend API)
```

**Critical path:** Service Catalog -> Working Hours -> Online Booking -> Client Database -> SBP Payment -> Auto Tax Receipt

This dependency chain defines the MVP build order. Every feature downstream requires the upstream feature to function.

---

## MVP Recommendation

**Must ship in v1 (table stakes + core differentiators):**

1. Service catalog (name, duration, price)
2. Master schedule (working hours, days off, breaks)
3. Online self-booking via mini-app (slot calculation, conflict prevention)
4. Client database (auto-populated from bookings, phone-based identity)
5. Booking confirmations + automated reminders (24h, 2h via bot)
6. Booking management (client cancel/reschedule, master override)
7. SBP payment link via Robokassa (master taps "Complete" -> client gets link)
8. Auto tax receipt via Robochecks ("Moy Nalog" integration)
9. At least TG bot + TG mini-app (fastest to build, largest audience)
10. Basic web admin panel (schedule view, client list, service management)

**Ship in v1.1 (fast follow, within 2-4 weeks of launch):**

11. MAX bot + MAX mini-app (time-sensitive window, spring 2026)
12. VK bot + VK mini-app (completes the multi-messenger story)
13. Cross-messenger client identity merge

**Defer to v2:**

- Revenue analytics (income per period, repeat rate)
- Client notes & tags
- Photo portfolio
- Repeat visit invitations ("You haven't visited in 30 days")
- Income/expense tracking
- Review collection
- Loyalty basics

---

## Competitive Pricing Context

Understanding competitor pricing informs feature scoping:

| Competitor | Price (solo master) | Has Booking | Has Payments | Has Auto Receipt | Has Multi-Messenger |
|------------|---------------------|-------------|--------------|------------------|---------------------|
| YCLIENTS | 270-686+/mo | Yes | Yes (YuKassa, manual setup) | No | No (web widget + maps) |
| DIKIDI | 450+/mo (free tier exists) | Yes | No native (external) | No | No (own app + web) |
| EasyWeek | Free tier + paid | Yes | Partial | No | No (web widget) |
| Okoshki | 490/mo | Yes | No | No | No (web page) |
| Beauty-Bot | 990+/mo + 7000 setup | Yes (TG only) | No | No | TG only |
| samoCRM | Free tier | No (CRM only) | Partial | Yes ("Moy Nalog") | No |
| Master CRM (mcrm.su) | Free tier | No (accounting) | No | Yes ("Moy Nalog") | No |
| ZapishiMenya | 390/mo | Yes (TG Mini App) | No | No | TG only |
| **This product** | **99/mo (planned)** | **Yes** | **Yes (SBP/Robokassa)** | **Yes (Robochecks)** | **Yes (TG+MAX+VK)** |

The planned 99/mo price point significantly undercuts all competitors while offering the only complete booking+payment+receipt+multi-messenger solution.

---

## Sources

### Competitor Analysis
- [YCLIENTS official site](https://www.yclients.com/)
- [YCLIENTS features overview on pickTech](https://picktech.ru/product/yclients/)
- [YCLIENTS knowledge base](https://support.yclients.com/1-2-91--1/)
- [DIKIDI features on pickTech](https://picktech.ru/product/dikidi/)
- [DIKIDI official features list](https://support.dikidi.net/ru/knowledge-bases/4/articles/176-osnovnyie-funktsii-prilozheniya-dikidi-online)
- [DIKIDI February 2026 updates](https://support.dikidi.net/ru/knowledge-bases/4/articles/1401-reliz-obnovlenij-dikidi-fevral-2026)
- [DIKIDI reviews (77 reviews)](https://crmindex.ru/products/dikidi/reviews)
- [YCLIENTS reviews (118 reviews)](https://crmindex.ru/products/yclients/reviews)
- [DIKIDI vs YCLIENTS comparison](https://vc.ru/opinions/1664675-dikidi-i-yclients-kakoi-instrument-luchshe-dlya-vas)
- [EasyWeek features](https://easyweek.ru/features)
- [Okoshki official site](https://okoshki.me)
- [Okoshki creation story on TBank](https://secrets.tbank.ru/blogi-kompanij/ot-idei-do-zapuska-okoshki/)
- [Beauty-Bot official site](https://bot-beauty.ru/)

### Self-Employed & Tax Integration
- [Robokassa Robochecks SMZ](https://robokassa.com/online-check/robocheck-smz/)
- [Robokassa for self-employed](https://robokassa.com/solutions/business/samozanyatye/)
- [samoCRM for self-employed](https://samocrm.ru/)
- [Master CRM (mcrm.su)](https://mcrm.su/)
- [CRM for self-employed 2026 guide on DataLopata](https://datalopata.ru/blog/crm-sistema-dlja-samozanjatyh-gid-po-avtomatizatsii-v-2026/)
- [Best CRMs for self-employed on vc.ru](https://vc.ru/topstud/2726353-luchshie-crm-dlya-samozanyatyh-i-fizicheskih-lits)
- [Prodamus for self-employed](https://prodamus.ru/priem-platezhej-dlya-samozanyatyh)

### Messenger Platforms
- [MAX for business](https://business.max.ru/)
- [MAX business opening spring 2026 (Kommersant)](https://www.kommersant.ru/doc/8401240)
- [MAX for business overview on OkoCRM](https://okocrm.com/blog/max-dlya-biznesa-vozmozhnosti-messendzhera/)

### Telegram Bots & Mini-Apps
- [ZapishiMenya (master's story on vc.ru)](https://vc.ru/services/2313524-kak-sozdat-telegram-bota-dlya-zapisi-klientov)
- [Mira business assistant](https://mira.by/)
- [Salebot for beauty salons](https://cases.salebot.pro/chat-bot-dlya-salona-krasoty)
- [Top 11 booking services 2026](https://vc.ru/services/2621340-top-11-prilozheniy-dlya-onlayn-zapisi-klientov-top-11-luchshih-platnyh-i-besplatnyh-reshenii)

### Industry Data
- [CRM scheduling features importance (94% of users rate as critical)](https://zeeg.me/en/blog/post/crm-scheduling)
- [75% of clients book online, 40% after hours](https://zeeg.me/en/blog/post/crm-scheduling)
- [CRM for small business features 2026](https://www.onepagecrm.com/blog/crm-features/)
