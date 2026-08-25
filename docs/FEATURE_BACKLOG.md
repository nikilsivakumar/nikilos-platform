# NikilOS — Feature Backlog & Stage Map

Companion to `docs/DOMAIN_MODEL.md` (which owns the data model/RBAC — don't duplicate decisions across both files, this one owns *what gets built*, that one owns *how data is structured*).

Last updated: 2026-08-25

---

## 1. Broad stages — where we are

| Stage | What | Status |
|---|---|---|
| 0 | Domain model, RBAC design, stack lock | ✅ Done |
| 1 | Core models: `users`, `coach_profiles`, `coach_clients`, `coach_billing`, `client_intro` + migrations | ✅ Done (4 commits on GitHub) |
| 2 | Permission logic (`get_access_level`, `require_access`) + RBAC test suite | 🔶 Written, **not yet confirmed committed** — verify tonight before moving on |
| 3 | Auth: signup/login, JWT, Google OAuth, wire `require_access` to real auth | ⬜ Next (build-sprint Week 1–3) |
| 4 | Core CRUD: `daily_logs`, `plans`, `plan_metrics`, `routines`, `workout_sessions`, `workout_sets`, `exercise_catalog` | ⬜ Week 4–6 |
| 5 | Coach-facing endpoints: client list, accept/reject, assign plan/routine | ⬜ Week 7 |
| 6 | Individual-facing endpoints: browse coaches, request coaching | ⬜ Week 8 |
| 7 | Dashboard aggregation endpoints: compliance score, weekly summary, body photos | ⬜ Week 9 |
| 8 | Hosting: VPS, HTTPS, backups | ⬜ Week 10 |
| 9 | Testing/QA pass | ⬜ Week 11 |
| 10 | Dogfooding — you use it daily, bugs only, no new features | ⬜ Nov 2026 – Jan 2027 |
| 11 | Frontend: React web dashboard (individual + coach) | ⬜ From Jan 2027 |
| 12 | Content launch, first real outside users | ⬜ From Jan 2027 |
| 13 | Owner/Admin dashboard | ⬜ Deferred until real usage exists |
| 14 | Billing enforcement (coach_billing tier check wired into accept-client flow) | ⬜ Deferred until actually monetizing |
| 15 | Mobile app (React Native/Expo) | ⬜ Deferred, Year 2+ |

---

## 2. Locked features — in scope for v1, already decided

Nothing here should be relitigated without a real reason — these came out of the domain-model + RBAC discussion and match your original requirements (multi-user, individual-or-coached, strict client isolation).

### Individual (every user has this, coach or not)
- Sign up / log in (email+password, Google OAuth)
- Log workouts: sessions, sets, weight/reps, estimated 1RM (Epley formula)
- Create own routines (exercise templates)
- Log daily metrics: weight, macros, calories, steps, sleep
- Set own plan + targets (calories, protein, steps, sleep) if no coach
- Personal dashboard: today's snapshot + trends + compliance score
- Body progress photos
- Browse public coach profiles
- Request coaching from a coach (creates `client_intro`)

### Coach (any user with a `coach_profile`)
- Public coach profile (bio, specialties, capacity)
- View pending requests — intro info only (goals, experience level), not full logs
- Accept / reject a request
- Full access to active clients' data
- Assign a plan/routine to a client
- Coach dashboard: client list + per-client drill-in
- Slot count vs `coach_billing.included_slots`

### Shared / platform
- Exercise catalog + aliases (shared reference data)
- Compliance scoring, always computed from DB-stored targets, never hardcoded
- Strict isolation: clients invisible to each other; coaches only see their own active/pending clients (enforced by `require_access`, already tested)

### Deferred but designed-for (schema exists, logic doesn't yet)
- Billing tiers: 15 free client slots, paid overage (`coach_billing` table built; enforcement logic — the actual "block accept until paid" check — not built)
- Owner/Admin analytics

---

## 3. Possible features — full brainstorm, undecided

Nothing below is committed. Purpose of this list is so nothing gets forgotten and every addition is a conscious choice, not a drift. Grouped so you can triage by category in Trello.

### UX / personalization
- Dark mode / light mode
- Unit preference (kg/lb, cm/in)
- Custom quick-log widget (mobile home screen)
- Push/email reminders (missed a log, check-in due)
- Multi-language toggle

### Progress & data depth
- Body measurements beyond weight (waist, chest, arms, etc.)
- Before/after photo slider
- Per-lift 1RM progression charts
- Training volume/tonnage per muscle group
- Macro breakdown visualizations
- Correlation views (sleep vs. compliance, etc. — this existed as stub pages in the old Streamlit build, could be revived here)
- Weekly/monthly PDF report export
- Raw data export (CSV/JSON) — worth prioritizing over most of this list; it's a direct expression of your "own your data, no platform lock-in" principle, cheap to build, and differentiates you from apps that trap your data
- Wearable integration (Apple Health, Google Fit, Garmin, Whoop) — large scope, treat as its own future project, not a checkbox
- Barcode food scanning — MyFitnessPal-scale feature, likely out of scope entirely unless nutrition logging becomes a core differentiator

### Coaching / business
- In-app coach↔client messaging
- Video form-check upload/review
- In-app payment collection (Razorpay/Stripe) for coaching fees
- Automated invoicing
- Weekly subjective check-in forms (energy, motivation, stress — not just physical metrics)
- Private coach notes on a client
- Reusable program/routine template library
- Waitlist when a coach is at capacity
- Public testimonials/reviews on coach profile
- **2-coach practice model** — flagging this one specifically: your stated business plan includes a 2-coach system at scale, but the current data model ties a client to exactly one coach via `coach_clients`. Supporting a "practice" where two coaches share visibility into the same client pool is a real architectural addition (a `coach_teams` concept), not a small toggle — worth deciding deliberately when you actually approach that scale, not bolting on later under pressure.

### Engagement — flag before building any of these
- Streaks, badges, achievements
- Leaderboards
- Milestone auto-celebrations

Worth naming directly: your original project philosophy (from the v0.1 blueprint) was explicitly "no social feed, no followers, no likes, no engagement farming." Streaks and badges sit close to that line — mild ones (a private streak counter just for you) are probably fine; anything comparing users to each other (leaderboards) contradicts the stated philosophy outright. Decide these with that tension in mind, not just "would this be fun to build."

### Owner/Admin (when Stage 13 actually happens)
- Revenue, churn, active user/coach counts
- Feature usage analytics
- System health / error monitoring (early on, just use your hosting provider's own dashboard — don't build this custom until you actually need more than that)
- Coach performance overview (relevant once the 2-coach model exists)
- Duplicate-account / fraud pattern flags (from the billing discussion — admin-side detection, not DB-side prevention)

### Technical / infra
- Offline-first local sync (explicitly a Year 3+ idea per your own roadmap — don't pull it forward)
- Rate limiting / abuse protection
- Automated DB backups (this one should NOT stay in "possible" — move to Stage 8, it's basic hygiene, not a feature)
- Audit log (useful if a coach/client dispute ever needs "who changed what, when")

---

## 4. Dashboards — what each role actually sees

### Individual dashboard
- **Today's snapshot**: weight, calories/macros vs. target, steps, sleep vs. target, compliance score for the day
- **Trends**: weight over time, compliance trend, 1RM/volume progression
- **Today's workout**: assigned (if coached) or self-selected routine, with a quick-log action
- **Coach card**: if coached, shows coach info + relationship status; if not, a "browse coaches" entry point
- **Progress photos**: timeline/gallery

### Coach dashboard
- **Client list**: active clients with an at-a-glance compliance indicator (e.g. simple red/amber/green) so you know who needs attention without opening each one
- **Pending requests queue**: intro info only — goals, experience level
- **Client detail view**: opening a client shows the *same components* as the individual dashboard, just for them — not a separately built view (see §5)
- **Capacity indicator**: slots used vs. `coach_billing.included_slots`
- **Assign action**: push a plan/routine to a selected client

### Owner/Admin dashboard (Stage 13, deferred)
- Total users/coaches/active clients, growth over time
- Revenue overview (once billing enforcement exists)
- Coach directory (moderation, in case a public profile needs review)

---

## 5. How the dashboards actually get built

**Order:** Individual dashboard first (also doubles as your own dogfooding tool during the Nov–Jan phase), then coach dashboard, then admin last — matches the stage table above.

**Approach:** build a small shared component library once — a metric card, a trend chart, a compliance ring, a client-list row — and reuse it across all three dashboards rather than building three separate UIs. The coach's "client detail view" and the individual's own dashboard should literally be the same component, just pointed at a different `user_id` (which `require_access` already gates correctly). This avoids tripling the frontend work for what's functionally the same data displayed to a different viewer, and keeps everything understandable end-to-end rather than three parallel codebases to maintain.

React web app first, per the locked stack — mobile (Expo) comes later, reusing the same backend endpoints, not rebuilt from scratch.

---

## 6. Tracking — Trello vs. alternative

**Recommendation: GitHub Projects (Projects v2), not Trello, as the primary tracker.**

Reasoning, since you asked for the actual call rather than just "either works":
- It's free, and it's already sitting inside the repo you're using — no second account, no sync problem between "what the board says" and "what the code says."
- Cards can link directly to commits/PRs — when a feature actually ships, the card can close itself rather than you remembering to update Trello separately.
- Supports custom fields (Stage, Priority, Status) close enough to Trello's list/label model that you lose nothing in usability.

Trello is a fine tool in general, but for a solo technical build tightly coupled to one repo, it adds a second system you have to keep in sync by hand — exactly the kind of overhead your own philosophy (feature bloat, avoiding unnecessary complexity) argues against. If you specifically want Trello for a lighter mobile-glance view, that's a legitimate reason — but I'd treat this doc as the actual source of truth either way, and whichever tracker you pick as just a thin view into it.

**Setup, either way:**
- GitHub Projects: go to the repo → **Projects** tab → **New project** → Board view. Create columns matching the stage table in §1 (Backlog / In Progress / Done, or one column per stage if you want finer granularity).
- Trello: import is provided below if you'd rather use it.
