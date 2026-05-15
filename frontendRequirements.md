# Flex — Frontend Requirements

> Companion document to [README.md](README.md) and [requirements.md](requirements.md).
> This is the brief you (or a V0 agent) will work from to build the Next.js
> frontend that consumes the Flex backend.

The frontend lives in **a separate repository** and ships **two surfaces** from
one Next.js codebase:

- **Tenant marketplace** (`/`, `/properties`, `/properties/[id]`, `/bookings`)
- **Landlord dashboard** (`/dashboard/*`)

Which surface a user sees is decided by the `role` claim on their JWT after
login. Public pages (landing, browse, property detail) are visible to anyone.

---

## 1. Tech stack

| Concern              | Choice                                                     |
| -------------------- | ---------------------------------------------------------- |
| Framework            | **Next.js 15+ (App Router)**, TypeScript strict            |
| Styling              | **Tailwind CSS** + CSS variables for theme tokens          |
| Components           | **shadcn/ui** (Radix primitives) — copy in, customizable   |
| Icons                | **lucide-react**                                           |
| Forms                | **react-hook-form** + **zod** for schema validation        |
| Data fetching        | **@tanstack/react-query** (server state) + native fetch    |
| Date handling        | **date-fns** (or **dayjs**) + **react-day-picker**         |
| Auth storage         | JWT in **httpOnly cookie** via a tiny Next.js route handler; never in `localStorage` |
| Notifications/Toasts | **sonner**                                                 |
| Maps (optional v1.1) | Leaflet + OpenStreetMap (no API key needed)                |

> If V0 cannot scaffold the cookie-based auth bridge, fall back to in-memory
> token storage with a thin `<AuthProvider>` — but never `localStorage`.

---

## 2. Design system

The product should feel **calm, spacious, editorial** — closer to Airbnb / Linear
than to a SaaS dashboard. Lots of whitespace. Generous line-height. Crisp,
restrained color.

### 2.1 Palette

A **white-first** UI with **black** for text/structure and **green** as the
single accent (CTAs, status highlights, selected states).

| Token            | Light value | Use                                              |
| ---------------- | ----------- | ------------------------------------------------ |
| `--bg`           | `#FFFFFF`   | Page background                                  |
| `--surface`      | `#FAFAFA`   | Cards, raised sections                           |
| `--surface-2`    | `#F4F4F5`   | Subtle blocks, skeletons                         |
| `--border`       | `#E5E7EB`   | Dividers, input borders                          |
| `--text`         | `#0A0A0A`   | Primary text                                     |
| `--text-muted`   | `#525252`   | Secondary text                                   |
| `--text-subtle`  | `#8A8A8A`   | Captions, helper text                            |
| `--accent`       | `#16A34A`   | Primary CTA, links, focus rings, selected dates  |
| `--accent-hover` | `#15803D`   | Hover/active for accent                          |
| `--accent-soft`  | `#DCFCE7`   | Accent-tinted backgrounds, badges                |
| `--danger`       | `#DC2626`   | Destructive actions, errors                      |
| `--warning`      | `#D97706`   | Pending / awaiting-action states                 |

A **dark mode** variant is nice-to-have, not required for v1. If included, swap
`--bg` to `#0A0A0A`, `--text` to `#FAFAFA`, keep accent identical.

### 2.2 Typography

- **Font:** `Inter` via `next/font/google` — weights 400, 500, 600, 700.
- **Display headings** (`h1` on landing / property detail): `text-5xl md:text-6xl`, `tracking-tight`, `font-semibold`.
- **Section headings** (`h2`): `text-2xl md:text-3xl`, `font-semibold`.
- **Body:** `text-base leading-relaxed` (`text-[15px]` on dense dashboard tables is fine).
- **Numbers / prices:** tabular-nums (`font-variant-numeric: tabular-nums`).

### 2.3 Spacing & layout

- Page container: `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8`.
- Vertical rhythm between sections on marketing/detail pages: `py-16 md:py-24`.
- Dashboard inner padding: `p-6 md:p-8`.
- Card padding: `p-5` (compact) or `p-6` (default).
- Radius scale: `rounded-lg` (8px) default, `rounded-xl` (12px) for cards, `rounded-2xl` (16px) for hero panels, `rounded-full` for chips/avatars.
- Shadows: avoid heavy shadows. Use `shadow-sm` and a subtle hover lift (`hover:shadow-md transition`). Borders > shadows for separation.

### 2.4 Motion

- Hover transitions: 150ms ease-out.
- Page transitions: none (keep Next.js default).
- Skeleton loaders for any network-bound content (`animate-pulse` on `--surface-2`).
- Avoid bouncy springs — restrained, professional.

### 2.5 Imagery

- Property photos are square-cropped (1/1) in cards, 16/10 on detail hero.
- Use `next/image` with `priority` on above-the-fold images only.
- Gallery: first image is large (left), next 2-4 are smaller thumbnails (right) — Airbnb-style grid on `md+`, single full-width carousel on mobile.

### 2.6 Components (shadcn/ui inventory)

Install these: `button`, `input`, `label`, `textarea`, `select`, `dialog`,
`sheet`, `dropdown-menu`, `tabs`, `card`, `badge`, `avatar`, `separator`,
`skeleton`, `tooltip`, `popover`, `calendar`, `form`, `toast` (or sonner),
`navigation-menu`, `table`.

---

## 3. Information architecture

### Tenant routes (public unless noted)

| Route                          | Purpose                                                  |
| ------------------------------ | -------------------------------------------------------- |
| `/`                            | Landing / hero search                                    |
| `/properties`                  | Browse + filter (city, dates, price, guests)             |
| `/properties/[id]`             | Detail: gallery, info, calendar, booking widget          |
| `/properties/[id]/book`        | Booking confirmation + checkout (auth required)          |
| `/bookings`                    | My bookings list (auth, tenant)                          |
| `/bookings/[id]`               | Booking detail (auth, tenant)                            |
| `/login`                       | Login                                                    |
| `/signup`                      | Signup (role chooser inside)                             |

### Landlord routes (auth + role=LANDLORD)

| Route                                  | Purpose                                |
| -------------------------------------- | -------------------------------------- |
| `/dashboard`                           | Overview: KPIs, recent bookings        |
| `/dashboard/properties`                | List own properties                    |
| `/dashboard/properties/new`            | Create property                        |
| `/dashboard/properties/[id]`           | Edit property                          |
| `/dashboard/bookings`                  | Inbox of received bookings + filters   |
| `/dashboard/bookings/[id]`             | Booking detail + accept/decline/cancel |
| `/dashboard/settings`                  | Profile + phone for SMS                |

### Route protection

- Middleware in `middleware.ts` reads the JWT from cookie:
  - Unauthenticated request to `/bookings/*` or `/dashboard/*` → redirect `/login?next=…`.
  - `role=TENANT` hitting `/dashboard/*` → redirect `/`.
  - `role=LANDLORD` hitting `/bookings` (tenant inbox) → redirect `/dashboard/bookings`.

---

## 4. Pages — tenant side

### 4.1 Landing `/`

- Full-bleed hero (no image, just typographic): "Find stays you'll actually want to come back to."
- Centered **search bar** floating over the hero: `city` input + `check-in` + `check-out` (date range popover) + `guests` stepper + green search button → routes to `/properties?city=…&check_in=…&check_out=…&guests=…`.
- Below: "Popular cities" chip row (static for v1), then a 3-column grid of 6 featured properties (calls `GET /properties?limit=6`).
- Footer: minimal — logo, copyright, link to sign up as host.

### 4.2 Browse `/properties`

- Left rail (desktop) / bottom sheet (mobile) of filters: city, date range, price min/max, guests.
- Main grid: responsive — 1 col mobile, 2 cols md, 3 cols lg, 4 cols xl.
- Each `PropertyCard`: square image, title, city, "$X / night" right-aligned, capacity row (beds / baths / guests).
- Empty state: friendly illustration text, "Try widening your dates."
- Skeleton grid on initial load.
- URL is the source of truth for filters (use `useSearchParams` + replace).

### 4.3 Property detail `/properties/[id]`

Layout (md+):

```text
┌────────────────────────────────────────────────────────┐
│  Title · city                                          │
│  ┌──────────────┬───────────────┐                      │
│  │              │  thumb │ thumb│  ← Airbnb gallery    │
│  │   big photo  ├────────┼──────┤                      │
│  │              │  thumb │ thumb│                      │
│  └──────────────┴────────┴──────┘                      │
│                                                        │
│  ┌─────────────────────────┬───────────────────────┐   │
│  │ Description, amenities, │  ┌─────────────────┐  │   │
│  │ host info, calendar of  │  │ Booking widget  │  │   │
│  │ unavailable dates       │  │  (sticky)       │  │   │
│  │                         │  │ dates · guests  │  │   │
│  │                         │  │ total · CTA     │  │   │
│  │                         │  └─────────────────┘  │   │
│  └─────────────────────────┴───────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

Booking widget rules:

- Date range picker disables ranges from `unavailable_dates` returned by the detail endpoint.
- Live total: `nights × price_per_night` (use tabular-nums).
- "Reserve" button → if not logged in, route to `/login?next=/properties/[id]/book?…`; otherwise route to checkout page.
- On mobile, the widget collapses into a sticky bottom bar with price + "Reserve" → opens a sheet with the same fields.

### 4.4 Checkout `/properties/[id]/book`

- Two-column on desktop, stacked on mobile.
- Left: guest details form (`full_name`, `phone`, `guest_count`, `guest_notes`), then a "Payment" card showing a fake card form (number / exp / cvc — purely visual, **do not capture or send**). Above the card form, a muted note: "Mock payment — no real card needed."
- Right: **price summary card** (sticky) with property thumb, dates, nightly × nights line, total, and a green "Confirm and pay" button.
- Submit flow:
  1. `POST /api/v1/bookings` → returns booking with `status=PENDING_PAYMENT`.
  2. `POST /api/v1/payments/intent` with `booking_id` → returns `{ intent_id, client_secret }`.
  3. `POST /api/v1/payments/mock/confirm` with `intent_id` → backend posts itself a webhook; booking flips to `PENDING_APPROVAL`.
  4. Frontend polls `GET /api/v1/bookings/{id}` (or refetches via React Query with `refetchInterval: 1500` for max 8s) until status is `PENDING_APPROVAL`, then redirects to `/bookings/[id]?paid=1`.
- Loading: full-page step indicator ("Creating booking… Confirming payment… Almost done…").
- Error: inline alert at top of form, allow retry.

### 4.5 My bookings `/bookings` and `/bookings/[id]`

- List: status pill (color-coded — see §6), property thumb, dates, total, primary action.
- Detail: full booking info, status timeline, payment + refund history (`GET /payments/booking/{booking_id}`), "Cancel booking" button (only when status is `PENDING_PAYMENT | PENDING_APPROVAL | CONFIRMED`).
- Tenant cancel confirms in a dialog that explicitly says "No refund will be issued" (matches FR-B8).

### 4.6 Auth pages

- Centered card, max width 420px, generous padding.
- `/signup` includes a role chooser at the top — two large radio cards: "I'm looking for a place" (TENANT) vs "I'm a host" (LANDLORD). Phone field required (E.164 placeholder: `+15551234567`).
- After signup OR login, redirect by role: TENANT → `next` or `/`; LANDLORD → `/dashboard`.
- Show a single inline error block on submit failures; no field-level server errors needed for v1.

---

## 5. Pages — landlord side

### 5.1 Dashboard overview `/dashboard`

- Three KPI cards across the top: **Properties**, **Pending approval**, **Confirmed (next 30d)**.
- A "Needs your action" panel listing bookings in `PENDING_APPROVAL` with quick Accept / Decline buttons inline.
- "Recent activity" timeline (last 10 status transitions on your bookings).

### 5.2 Properties `/dashboard/properties`

- Table on desktop, card list on mobile. Columns: image, title, city, price/night, bookings count, status (active), actions menu (edit, delete with confirm).
- Green "New property" button top-right routes to `/dashboard/properties/new`.

### 5.3 Property form `/dashboard/properties/new` and `/[id]`

- Sections, each in its own card:
  1. **Basics:** title, description (textarea), city, country, address.
  2. **Pricing:** price_per_night, currency (select, default USD).
  3. **Capacity:** max_guests, bedrooms, bathrooms (steppers).
  4. **Amenities:** multi-select chips from a fixed list (Wifi, Kitchen, Parking, Pool, Washer, A/C, Heating, Workspace, TV, Pets allowed, Smoke alarm).
  5. **Photos:** repeating list of **image URL inputs** (not file uploads — backend stores URLs only). Live thumbnail preview next to each input. "Add another URL" button.
- Sticky footer with Cancel / Save.
- Form validation via zod — show errors inline under each field.

### 5.4 Bookings inbox `/dashboard/bookings`

- Tabs across the top: `Needs action` (default — `PENDING_APPROVAL`), `Upcoming` (`CONFIRMED`, check-in >= today), `Past`, `Cancelled / declined`.
- List of `BookingRow` items: tenant name + avatar, property name, dates, total, status pill, primary CTA per tab.
- Detail page mirrors tenant booking detail but with landlord-only actions:
  - `PENDING_APPROVAL` → **Accept** (green) and **Decline** (outlined red).
  - `CONFIRMED` → **Cancel booking** (outlined red, confirm dialog says "Full refund will be issued").
- Confirm dialogs are non-skippable; destructive buttons are not auto-focused.

### 5.5 Settings `/dashboard/settings`

- Profile (name, email read-only, phone editable).
- Note: "We use your phone number for booking SMS alerts via Twilio."

---

## 6. Status pills & state language

A single source of truth for booking status. Pill = `--accent-soft` for positive,
`--surface-2` + muted text for neutral, light red tint for terminal-negative.

| Status              | Label             | Color band                                   |
| ------------------- | ----------------- | -------------------------------------------- |
| `PENDING_PAYMENT`   | Awaiting payment  | neutral (`--surface-2` / `--text-muted`)     |
| `PENDING_APPROVAL`  | Awaiting host     | warning (amber tint, `--warning` text)       |
| `CONFIRMED`         | Confirmed         | accent (`--accent-soft` / `--accent-hover`)  |
| `DECLINED`          | Declined          | danger (red-50 / `--danger`)                 |
| `CANCELLED`         | Cancelled         | danger (red-50 / `--danger`)                 |
| `EXPIRED`           | Expired           | neutral                                      |

---

## 7. Mobile responsive requirements

- Design **mobile-first**. Test breakpoints: 360, 414, 768, 1024, 1280, 1536.
- No horizontal scroll at any breakpoint.
- Tap targets ≥ 44×44px.
- Property detail booking widget collapses to a sticky bottom bar on `< md`.
- Landlord tables become stacked cards on `< md`.
- Filters on `/properties` become a "Filters" button that opens a bottom `Sheet` on `< md`.
- Navigation is a hamburger sheet on `< md`, full nav bar from `md+`.

---

## 8. API contract

### 8.1 Base configuration

- Base URL via env: `NEXT_PUBLIC_API_BASE_URL` (e.g. `http://localhost:8000/api/v1`).
- Default headers: `Content-Type: application/json`, `Accept: application/json`.
- Auth header on protected calls: `Authorization: Bearer <jwt>`.
- All timestamps are **ISO 8601 UTC** strings.
- All money fields are decimal strings with 2 decimals (e.g. `"129.00"`) — never parse as float for display; treat as strings, format via `Intl.NumberFormat`.
- Errors come back as:

```json
{ "error": { "code": "BOOKING_OVERLAP", "message": "Those dates are not available." } }
```

  Always render `error.message`. Use `error.code` for special-casing (e.g. show
  the date picker when `BOOKING_OVERLAP`).

### 8.2 Endpoints

> Full spec is in [requirements.md §6](requirements.md). Below is the
> consumer-side TypeScript view of every call the frontend makes.

#### Auth

```ts
POST /auth/signup
body: {
  email: string;
  password: string;
  full_name: string;
  role: "TENANT" | "LANDLORD";
  phone_number: string; // E.164
}
→ 201 { id, email, full_name, role, phone_number, created_at }

POST /auth/login
body: { email: string; password: string }
→ 200 { access_token: string; token_type: "bearer"; expires_at: string }

GET /auth/me   (auth)
→ 200 { id, email, full_name, role, phone_number, created_at }
```

#### Properties

```ts
GET /properties
query?: {
  city?: string;
  min_price?: number; max_price?: number;
  guests?: number;
  check_in?: string; check_out?: string;   // YYYY-MM-DD
  limit?: number; offset?: number;
}
→ 200 {
  items: Property[];
  total: number;
  limit: number;
  offset: number;
}

GET /properties/{id}
→ 200 Property & { unavailable_ranges: Array<{ start: string; end: string }> }

POST /properties           (auth, LANDLORD)
PATCH /properties/{id}     (auth, LANDLORD, own)
DELETE /properties/{id}    (auth, LANDLORD, own)
GET /properties/mine       (auth, LANDLORD) → { items: Property[] }

type Property = {
  id: string;
  landlord_id: string;
  title: string;
  description: string;
  city: string;
  country: string;
  address: string;
  price_per_night: string;  // decimal string
  currency: string;         // "USD"
  max_guests: number;
  bedrooms: number;
  bathrooms: number;
  amenities: string[];
  image_urls: string[];
  created_at: string;
  updated_at: string;
};
```

#### Bookings

```ts
POST /bookings              (auth, TENANT)
body: {
  property_id: string;
  check_in: string; check_out: string;   // YYYY-MM-DD
  guest_count: number;
  guest_notes?: string;
}
→ 201 Booking   // status will be "PENDING_PAYMENT"

GET /bookings/mine          (auth, TENANT)  → { items: Booking[] }
GET /bookings/received      (auth, LANDLORD) → { items: Booking[] }
GET /bookings/{id}          (auth, both)    → Booking
POST /bookings/{id}/accept  (auth, LANDLORD) → Booking
POST /bookings/{id}/decline (auth, LANDLORD) → Booking
POST /bookings/{id}/cancel  (auth, both)    → Booking

type BookingStatus =
  | "PENDING_PAYMENT" | "PENDING_APPROVAL" | "CONFIRMED"
  | "DECLINED" | "CANCELLED" | "EXPIRED";

type Booking = {
  id: string;
  property: { id: string; title: string; city: string; image_url: string | null };
  tenant: { id: string; full_name: string };
  check_in: string; check_out: string;
  nights: number;
  guest_count: number;
  guest_notes: string | null;
  total_amount: string;     // decimal string
  currency: string;
  status: BookingStatus;
  created_at: string;
  updated_at: string;
};
```

#### Payments

```ts
POST /payments/intent           (auth, TENANT)
body: { booking_id: string }
→ 201 { intent_id: string; client_secret: string; amount: string; currency: string }

POST /payments/mock/confirm     (auth, TENANT — dev/mock only)
body: { intent_id: string }
→ 202 { accepted: true }       // backend will then post its own webhook

GET /payments/booking/{booking_id}   (auth, both)
→ 200 {
    payments: Array<{ id; amount; currency; status; created_at }>;
    refunds:  Array<{ id; amount; currency; status; created_at }>;
  }
```

> The frontend **never** calls `/payments/webhook` directly — that endpoint
> exists only for the payment provider to call the backend.

---

## 9. Auth flow (frontend)

1. On `/login` submit, POST `/auth/login`.
2. On success, store the token by calling a Next.js route handler
   `POST /api/session` that sets an **httpOnly Secure cookie** (`flex_at`) with
   `SameSite=Lax`. The handler also returns `{ role }` so the client can route.
3. A client-side `<AuthProvider>` fetches `/auth/me` on mount (if cookie
   present) and caches it via React Query under key `["me"]`.
4. The shared `apiFetch(path, init)` helper reads the cookie server-side (in
   route handlers / RSC) or relies on the browser to send it (in client
   components) and attaches `Authorization: Bearer …` only when calling the
   backend from a Next.js route handler. **Client components never see the
   raw token.**
5. `middleware.ts` reads the cookie and decodes it without verifying
   (verification stays on the backend) to do role-based redirects.
6. Logout: `DELETE /api/session` clears the cookie, then `router.push("/")`.

> Why not localStorage: XSS-stealable tokens are the most common frontend
> security bug. httpOnly cookie + Next.js handler keeps the surface small.

---

## 10. Data fetching conventions

- React Query for **all server state**. No `useState` for fetched data.
- Query keys are tuples mirroring the resource: `["properties", filters]`,
  `["property", id]`, `["bookings", "mine"]`, `["bookings", "received", tab]`.
- Mutations call backend, then `invalidateQueries` on the affected keys.
- Use `placeholderData: keepPreviousData` on the browse grid so filtering feels instant.
- On every fetch, surface a skeleton, never a blank screen.
- On every mutation success, show a `sonner` toast (e.g. "Booking accepted —
  the tenant has been notified.").
- On every mutation error, show the backend's `error.message`. Never show
  raw HTTP codes.

---

## 11. Accessibility

- All interactive elements reachable via keyboard, visible focus ring in `--accent`.
- Color contrast meets WCAG AA (the chosen `--accent` `#16A34A` on `#FFFFFF` passes for non-text UI; for text-on-accent use `--accent-hover` `#15803D`).
- Date picker uses `react-day-picker` which is keyboard-accessible out of the box.
- All form fields have explicit `<label>` (no placeholder-as-label).
- All images have `alt`. Property images use `alt={`${property.title}, ${property.city}`}`.
- Status pills include `aria-label` so screen readers say the full status.

---

## 12. Project structure (frontend repo)

```text
flex-frontend/
├── app/
│   ├── (marketing)/             # public surfaces
│   │   ├── page.tsx             # landing
│   │   ├── properties/
│   │   │   ├── page.tsx
│   │   │   └── [id]/
│   │   │       ├── page.tsx
│   │   │       └── book/page.tsx
│   ├── (tenant)/                # auth-required tenant pages
│   │   └── bookings/
│   ├── (auth)/                  # login, signup
│   ├── dashboard/               # landlord
│   │   ├── layout.tsx           # sidebar + topbar
│   │   ├── page.tsx
│   │   ├── properties/
│   │   ├── bookings/
│   │   └── settings/
│   ├── api/
│   │   └── session/route.ts     # sets/clears httpOnly cookie
│   ├── layout.tsx               # root + providers
│   └── globals.css              # tailwind + theme tokens
├── components/
│   ├── ui/                      # shadcn primitives
│   ├── property/
│   ├── booking/
│   ├── dashboard/
│   └── nav/
├── lib/
│   ├── api.ts                   # apiFetch wrapper
│   ├── auth.ts                  # token cookie helpers
│   ├── format.ts                # money/date formatters
│   └── query.ts                 # React Query client
├── hooks/
├── types/
│   └── api.ts                   # mirrored backend types
├── middleware.ts
├── tailwind.config.ts
├── next.config.ts
└── .env.example                 # NEXT_PUBLIC_API_BASE_URL=...
```

---

## 13. Definition of done (frontend v1)

A frontend build is done when, against a running backend:

1. A new visitor can browse `/properties`, filter by city/dates/price/guests, and open a property detail.
2. A new tenant can sign up, log in, book a property, "pay" through the mock checkout, and see their booking move from `PENDING_PAYMENT` → `PENDING_APPROVAL` without a refresh.
3. A landlord can sign up, log in, land on `/dashboard`, create a property with image URLs, see the new booking in the inbox, accept it, and the tenant's `/bookings/[id]` view reflects `CONFIRMED` on next view.
4. The landlord can decline / cancel; the tenant detail shows the refund row and a "Cancelled" pill.
5. The UI works at 360px width with no horizontal scroll and no broken layout.
6. Lighthouse: Performance ≥ 85, Accessibility ≥ 95, Best Practices ≥ 95.

---

## 14. V0 agent prompt (paste this into V0)

Use the prompt below as the **initial prompt** in V0. It is self-contained and
matches every spec above. Iterate from there — V0 works best when you build one
page at a time, then ask it to refine.

````text
You are building the frontend for "Flex", an Airbnb-style short-stay booking
product. Build it as a Next.js 15 App Router + TypeScript project using
Tailwind CSS and shadcn/ui. The product has TWO surfaces from one codebase:
a TENANT marketplace and a LANDLORD dashboard, role-gated by a JWT claim.

DESIGN
- Theme: white-first, black for text/structure, GREEN as the single accent.
  Tokens (CSS variables on :root):
    --bg #FFFFFF, --surface #FAFAFA, --surface-2 #F4F4F5, --border #E5E7EB,
    --text #0A0A0A, --text-muted #525252, --text-subtle #8A8A8A,
    --accent #16A34A, --accent-hover #15803D, --accent-soft #DCFCE7,
    --danger #DC2626, --warning #D97706.
- Wire these into tailwind.config.ts as `theme.extend.colors` semantic tokens
  (bg, surface, border, text, accent, danger, warning) and use them everywhere
  instead of raw hex.
- Font: Inter via next/font/google, weights 400/500/600/700. Tabular numerals
  on prices.
- Vibe: calm, spacious, editorial — closer to Airbnb / Linear than to a SaaS
  dashboard. Lots of whitespace, generous line-height, restrained color.
  Borders > shadows for separation. Hover lift is `shadow-sm` -> `shadow-md`,
  150ms ease-out.
- Radius: rounded-lg default, rounded-xl cards, rounded-2xl hero panels.
- Container: max-w-7xl mx-auto px-4 sm:px-6 lg:px-8.
- MUST be mobile-first responsive. Test at 360, 414, 768, 1024, 1280. No
  horizontal scroll. Tap targets >= 44px.

DEPENDENCIES
- shadcn/ui components: button, input, label, textarea, select, dialog, sheet,
  dropdown-menu, tabs, card, badge, avatar, separator, skeleton, tooltip,
  popover, calendar, form, table, sonner (toasts).
- lucide-react, react-hook-form, zod, @tanstack/react-query, date-fns,
  react-day-picker.

PAGES (build in this order; ask me to confirm before each)

1) Public marketing
   - `/` landing: full-bleed hero with a single H1 ("Find stays you'll actually
     want to come back to."), centered floating search bar (city input,
     date-range popover for check-in/check-out, guests stepper, green Search
     button that routes to /properties with query params), a chip row of
     popular cities, and a 3-col grid of 6 featured properties.
   - `/properties` browse: left filter rail on desktop (city, date range,
     price min/max, guests), bottom-sheet "Filters" button on mobile.
     Responsive grid: 1/2/3/4 cols at sm/md/lg/xl. PropertyCard shows
     square image, title, city, "$X / night" right-aligned, and a meta row
     (beds / baths / guests). Empty state, skeleton grid.
   - `/properties/[id]` detail: Airbnb-style 5-image gallery on md+, single
     carousel on mobile. Two-column body: left = description, amenity grid,
     calendar of unavailable dates (read-only); right = sticky booking
     widget (date range picker that disables unavailable ranges, guests
     stepper, live total = nights * price_per_night, green "Reserve" CTA).
     On mobile, widget becomes a sticky bottom bar with price + "Reserve"
     that opens a Sheet.

2) Auth
   - `/login`: centered card 420px, email + password, link to /signup, single
     inline error block.
   - `/signup`: same shape but with a role chooser at top — two large radio
     cards: "I'm looking for a place" (TENANT) vs "I'm a host" (LANDLORD).
     Phone field required (E.164 placeholder +15551234567). After submit,
     redirect by role: TENANT → "/", LANDLORD → "/dashboard".

3) Checkout + bookings (tenant)
   - `/properties/[id]/book`: two-column on desktop. Left = guest form
     (full_name, phone, guest_count, guest_notes) then a fake card form
     (number/exp/cvc, purely visual, NO submission of card data) under a
     muted "Mock payment — no real card needed" note. Right = sticky price
     summary card (thumb, dates, nightly × nights, total, green "Confirm
     and pay"). Submit flow: POST /bookings → POST /payments/intent →
     POST /payments/mock/confirm → poll GET /bookings/{id} every 1.5s up to
     8s until status === "PENDING_APPROVAL" → redirect to /bookings/{id}.
     Full-page step indicator during the flow. Inline error alert with retry.
   - `/bookings` list and `/bookings/[id]` detail with status pill, timeline,
     payment + refund history, Cancel button (only for PENDING_PAYMENT,
     PENDING_APPROVAL, CONFIRMED). Cancel dialog says explicitly "No refund
     will be issued."

4) Landlord dashboard (sidebar layout with collapsible nav on md-)
   - `/dashboard`: 3 KPI cards (Properties, Pending approval, Confirmed next
     30d), "Needs your action" list of PENDING_APPROVAL bookings with inline
     Accept/Decline, "Recent activity" timeline.
   - `/dashboard/properties`: table on desktop / card list on mobile. Green
     "New property" button.
   - `/dashboard/properties/new` and `/[id]`: form sections (Basics,
     Pricing, Capacity, Amenities chips, Photos as repeating URL inputs with
     live thumbnail preview — NO file upload). Sticky footer Cancel/Save.
   - `/dashboard/bookings`: tabs (Needs action, Upcoming, Past,
     Cancelled/declined). BookingRow with tenant avatar+name, property,
     dates, total, status pill, primary CTA per tab.
   - `/dashboard/bookings/[id]`: full detail, Accept (green) / Decline
     (outlined red) on PENDING_APPROVAL, Cancel on CONFIRMED (confirm dialog
     says "Full refund will be issued"). Non-skippable destructive dialogs;
     destructive buttons not auto-focused.
   - `/dashboard/settings`: name, email (readonly), phone (editable). Helper
     text: "We use your phone number for booking SMS alerts via Twilio."

STATUS PILLS (use everywhere booking status is shown)
  PENDING_PAYMENT  "Awaiting payment"  neutral (surface-2 / text-muted)
  PENDING_APPROVAL "Awaiting host"     warning (amber tint / --warning)
  CONFIRMED        "Confirmed"         accent (--accent-soft / --accent-hover)
  DECLINED         "Declined"          danger
  CANCELLED        "Cancelled"         danger
  EXPIRED          "Expired"           neutral

API CONTRACT
- Base URL from `process.env.NEXT_PUBLIC_API_BASE_URL`.
- All responses JSON. Money is decimal strings ("129.00"), format with
  Intl.NumberFormat — never parseFloat for display.
- Errors are { error: { code, message } }. Always render error.message.
- All authed calls send Authorization: Bearer <jwt>.
- Endpoints used by the frontend (mirror these into /types/api.ts exactly):

  POST   /auth/signup    { email, password, full_name, role, phone_number }
  POST   /auth/login     { email, password } -> { access_token, token_type, expires_at }
  GET    /auth/me        -> User

  GET    /properties     query: city, min_price, max_price, guests, check_in,
                                check_out, limit, offset
                         -> { items: Property[], total, limit, offset }
  GET    /properties/:id -> Property & { unavailable_ranges: {start,end}[] }
  POST   /properties        (LANDLORD)
  PATCH  /properties/:id    (LANDLORD, own)
  DELETE /properties/:id    (LANDLORD, own)
  GET    /properties/mine   (LANDLORD)

  POST   /bookings                    (TENANT) -> Booking (PENDING_PAYMENT)
  GET    /bookings/mine               (TENANT)
  GET    /bookings/received           (LANDLORD)
  GET    /bookings/:id                (both)
  POST   /bookings/:id/accept         (LANDLORD)
  POST   /bookings/:id/decline        (LANDLORD)
  POST   /bookings/:id/cancel         (both — different rules per role)

  POST   /payments/intent             (TENANT)  -> { intent_id, client_secret, amount, currency }
  POST   /payments/mock/confirm       (TENANT)  -> { accepted: true }
  GET    /payments/booking/:id        (both)    -> { payments[], refunds[] }

AUTH STORAGE
- Store JWT in an httpOnly Secure cookie named `flex_at` set by a Next.js
  route handler POST /api/session (and cleared by DELETE /api/session).
- NEVER use localStorage for the token.
- middleware.ts decodes (does NOT verify) the cookie to do role-based
  redirects: unauthenticated -> /login?next=…; TENANT hitting /dashboard ->
  /; LANDLORD hitting /bookings -> /dashboard/bookings.

DATA FETCHING
- @tanstack/react-query for all server state. Query keys mirror the resource.
- Skeletons on every loading state, never blank screens.
- Toasts (sonner) on every mutation success/failure. Show error.message.
- Use placeholderData: keepPreviousData on the browse grid.

ACCESSIBILITY
- All interactive elements keyboard-reachable, visible focus ring in --accent.
- Explicit <label> on every field. alt on every image. aria-label on status
  pills. Color contrast WCAG AA.

DELIVERABLES
- A working `app/` with all routes above, even if some screens show seeded
  mock data via React Query's `initialData`.
- `tailwind.config.ts` with the semantic color tokens wired up.
- `types/api.ts` exporting Property, Booking, User, BookingStatus, ApiError.
- `lib/api.ts` with an `apiFetch` helper that reads the cookie server-side,
  attaches the bearer token, and throws typed ApiError on non-2xx.
- `lib/format.ts` with `formatMoney(amount: string, currency: string)` and
  `formatDateRange(start, end)`.
- `middleware.ts` doing the role redirects above.
- `.env.example` with NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1.

START by generating: (1) tailwind.config.ts + globals.css with the tokens,
(2) the root layout with Inter font and providers (QueryClientProvider,
Toaster), (3) the landing page `/`. Stop there and wait for review before
moving to /properties.
````

---

## 15. Things to watch for when reviewing V0 output

- It tends to inline colors as raw Tailwind classes (`bg-green-600`). Push it
  to use the semantic tokens (`bg-accent`) instead so theme changes are one
  file.
- It loves `shadow-lg` everywhere. Strip them down — the design is border-first.
- It may default to `localStorage` for the JWT. Reject and ask for the
  cookie + route handler approach.
- It will sometimes invent endpoints. Check every fetch URL against §8.2.
- It may use `parseFloat` on price strings. Reject — money stays as strings.
- It may forget the mobile bottom-bar variant of the booking widget. Spot-check `< md`.
