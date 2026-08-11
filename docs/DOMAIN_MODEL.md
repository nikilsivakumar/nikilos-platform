# NikilOS Platform — Domain Model & RBAC (Locked)

Status: **Locked as of 2026-08-04.** This is the single source of truth for entities and permissions. If it needs to change, change it here first, before touching code — that discipline caught the `phases`→`plans` mismatch in the previous build and it applies again here.

## Why this rebuild exists

Two prior codebases existed:
1. A local SQLite + Streamlit single-user tracker — retired, schema (`phases`) didn't support per-client plans.
2. A FastAPI + Postgres backend reported as built and auth-tested — never verified against any file the user actually possesses, and almost certainly lost because it lived only in an ephemeral session sandbox and was never committed to a durable repo.

This repo starts from a blank schema, and — critically — is committed to GitHub from the first scaffold commit so nothing lives only in a disposable session again.

## Core principle: one person, layered capabilities

There is no rigid "Individual / Coach / Client" caste system. **Every person is a `user`.** Role is *derived*, not stored:

- Every user can log their own workouts and nutrition, whether or not they have a coach.
- A user becomes a **coach** by having a `coach_profile` row (public-facing).
- A user becomes a **client of a specific coach** via a `coach_clients` row — this relationship, not an account type, is what grants a coach visibility into that user's data.
- A user can be a coach *and* independently log their own training as an individual — the model doesn't fight this.

This means `coach_clients` is the single permission boundary for the entire platform. Get that one table's enforcement right and the rest follows.

## Entities

| Entity | Purpose | Key fields |
|---|---|---|
| `users` | One row per person. Auth lives here. | id, email, hashed_password, google_id, name, created_at |
| `coach_profiles` | Extends a user into a public, browsable coach. | user_id (FK, unique), bio, specialties, capacity, is_public |
| `coach_clients` | The relationship + permission boundary. | coach_id, client_id, status (`pending`/`active`/`inactive`), requested_at, accepted_at |
| `client_intro` | Basic intro info visible to a coach *before* acceptance (goals, experience level) — not full logs. | coach_client_id (FK), goals_text, experience_level |
| `plans` | A training/nutrition block, self-made or coach-assigned. | id, owner_id, created_by, name, is_active, start_date, end_date |
| `plan_metrics` | Targets for a plan — relational, never JSON on the plan row. | plan_id, calorie_target, protein_target, step_target, sleep_target |
| `daily_logs` | One row per user per day. | user_id, date, weight_kg, protein_g, calories, steps, sleep_h, compliance_score |
| `routines` | Workout template — self-made or coach-assigned. | id, created_by, assigned_to, name |
| `routine_exercises` | Exercises within a routine, target sets/reps. | routine_id, exercise_id, target_sets, target_reps |
| `workout_sessions` | A logged training session. | user_id, routine_id (nullable), date, started_at, ended_at |
| `workout_sets` | Individual sets within a session. | session_id, exercise_id, set_index, weight_kg, reps, estimated_1rm |
| `exercise_catalog` | Shared reference data — not per-user. | id, name, category (loaded/bodyweight/bodyweight_assisted/no_1rm) |
| `exercise_aliases` | Alternate names mapping to catalog entries. | alias, exercise_id |
| `body_photos` | Progress photos, optionally tagged to a plan. | user_id, plan_id (nullable), date, file_path, angle |

## RBAC — permission matrix

| Actor | Can see | Cannot see |
|---|---|---|
| **Individual** (no coach, or pending request) | Own logs, own dashboard, public `coach_profiles` (browse-only) | Any other user's data |
| **Client** (`coach_clients.status = active`) | Own logs, own dashboard, their coach's public profile | Other clients of the same coach; any other coach's clients |
| **Coach** | Own dashboard; every client where `coach_clients.status = active`, full data; `client_intro` for `pending` requests (goals + experience level only) | Full logs of a `pending` (not-yet-accepted) requester; any client not linked to them via `coach_clients`; other coaches' clients |

### Enforcement rule

One dependency, reused everywhere, never bypassed per-route:

```
require_access_to_user(target_user_id, current_user):
    if current_user.id == target_user_id:
        return ALLOW  # full access, always
    row = coach_clients.get(coach_id=current_user.id, client_id=target_user_id)
    if row and row.status == "active":
        return ALLOW  # full access
    if row and row.status == "pending":
        return ALLOW_INTRO_ONLY  # client_intro fields only, not daily_logs/workout_sessions/etc.
    return DENY
```

This is the highest-stakes piece of logic in the whole platform — a bug here leaks one client's data to another client or to the wrong coach. It gets written once, tested explicitly (including negative tests: coach A must not see coach B's clients), and every route that touches another user's data calls it. No endpoint re-implements this check inline.

## What's locked vs. what's next

**Locked (this document):**
- Entity list and relationships above
- RBAC matrix and enforcement rule
- Stack: FastAPI + PostgreSQL + SQLAlchemy + Alembic

**Next (not yet built — requires confirmation before each step, per established workflow):**
1. SQLAlchemy models implementing the entities above
2. Alembic initial migration
3. Auth (signup/login/Google OAuth) + `require_access_to_user` dependency, with negative-case tests
4. CRUD: daily_logs, plans, routines, workout logging
5. Coach-facing endpoints: client list, accept/reject request, assign routine/plan
6. Individual-facing endpoints: browse coaches, request coaching
7. Frontend

Do not skip ahead to step N+1 while step N is unverified — this is the exact discipline that was missing when the previous FastAPI attempt was lost.
