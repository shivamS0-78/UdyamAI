# Supabase Auth (Email + Password) — Setup Guide

UdyamAI authenticates users through **Supabase Auth with email and
password**, replacing the old mock login. Sessions are enforced
end-to-end:

```
Next.js (Supabase client, email/password)
      │  access token
      ▼
FastAPI (verifies Supabase JWT, resolves the app profile)
      │
      ▼
PostgreSQL (RLS + profiles.autosynced from auth.users)
```

> Earlier iterations used a phone (+91) OTP flow (needed an SMS provider
> such as Twilio) and then an email OTP flow. Both were dropped in favor of
> plain email/password, which needs no paid provider and no SMS gateway.

## What was added

| Layer | Files |
| --- | --- |
| Database | `supabase/migrations/007_supabase_auth_profiles.sql` — auto-creates a `profiles` row on signup (`auth.users` trigger), syncs email/phone, adds missing profile columns, backfills existing users |
| Backend | `app/services/auth_service.py` (JWT verification), `app/api/deps.py` (`get_current_user` / `get_current_profile`), `app/api/routes/auth.py` (`GET /auth/me`) |
| Backend enforcement | `/analysis`, `/chat`, `/reports` require a valid session. All `/finance/*` routes resolve the profile from the session token (client-supplied `profile_id` is ignored), and child records are ownership-checked |
| Frontend | `@supabase/ssr` + `@supabase/supabase-js`, browser/server clients, `src/middleware.ts` route guard, `AuthProvider`, email/password `LoginForm` (sign in + create account), bearer token attached to all backend calls |

## 1. Supabase project configuration (dashboard, ~2 min)

1. **Enable email auth**
   `Authentication → Sign In / Providers → Email`: enable the **Email**
   provider. It is on by default for new projects.
2. **Decide on email confirmation.** With **Confirm email** enabled (the
   default) a new sign-up receives a confirmation link and cannot sign in
   until it is clicked — the app shows "check your inbox" after sign-up.
   For local development you can disable it
   (`Authentication → Sign In / Providers → Email → Confirm email`) so
   sign-ups get an instant session. Keep it enabled before real users.
3. Copy these from `Project Settings → API`:
   - **Project URL** → `NEXT_PUBLIC_SUPABASE_URL`
   - **anon public** key → `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - **JWT Settings → JWT Secret** → `SUPABASE_JWT_SECRET` (backend only)

> **Rate limits:** confirmation/password emails go out through Supabase's
> built-in email service, which is heavily rate-limited (a few emails per
> hour) — fine for development. Connect a custom SMTP provider
> (`Project Settings → Authentication → SMTP`) before onboarding real users.

## 2. Environment variables

**Frontend** (`frontend/.env.local` — copy `frontend/.env.example`):

```env
NEXT_PUBLIC_SUPABASE_URL=https://<project-ref>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon-public-key>
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Backend** (`backend/.env` and/or the repo-root `.env`, which
`app/config.py` already loads):

```env
SUPABASE_JWT_SECRET=<jwt-secret-from-settings>
```

## 3. Apply the database migration

```bash
cd supabase
supabase link --project-ref <project-ref>
supabase db push
```

Or run `supabase/migrations/007_supabase_auth_profiles.sql` in the
Supabase SQL editor. The migration:

- creates `profiles` rows automatically for every new `auth.users` row;
- keeps `profiles.email` / `profiles.phone` in sync on auth user updates;
- backfills `profiles` for users that signed up before the migration.

> Existing demo rows (e.g. the seeded `00000000-…-000000000001` profile)
> are not linked to real auth users and are no longer reachable through
> the API. A signed-in user gets their own profile row (created by the
> trigger) and starts with empty FinCompass data.

## 4. Run

1. Start the backend (`uvicorn app.main:app`).
2. Start the frontend (`npm run dev` inside `frontend/`).
3. Open `/login`:
   - **Create Account** to register an email/password (confirm the email
     first if "Confirm email" is on), then sign in;
   - or **Sign In** with an existing account.
   - On success you are redirected to `/setup` → `/dashboard`.
4. All user-data endpoints (`/analysis`, `/chat`, `/reports`,
   `/finance/*`) return `401` without a valid session, and `/auth/me`
   returns the session user plus their linked profile.

## Notes / follow-ups

- Reference-data endpoints (`/locations`, `/schemes`, `/markets`,
  `/business-categories`, …) remain public, matching the existing RLS
  "authenticated reads" model via the backend's service connection.
- `profiles.phone` is nullable and only populated when the user provides
  one (e.g. through the profile editor); email/password sign-up does not
  require it.
- Accounts created by the earlier email-OTP experiments have no password
  and cannot sign in until they set one (password reset is not wired into
  the UI yet — `supabase.auth.resetPasswordForEmail` would be the follow-up).
- Object-level authorization on analysis *read* endpoints is not yet
  enforced per-run (a signed-in user could in theory view another run by
  guessing its UUID); the routes do require a valid session. Wiring
  `run.user_id == profile.id` checks there is a small follow-up.
- Token verification in `app/services/auth_service.py` supports both
  **HS256** tokens (verified with `SUPABASE_JWT_SECRET`) and **ES256**
  tokens (verified against the project's public keys from
  `/auth/v1/.well-known/jwks.json`, cached with rotation fallback). Newer
  Supabase projects sign user access tokens with ES256, so the JWT secret
  alone is not enough to accept sessions.
- `tests/api/test_finance.py` fails independently of this change (it still
  targets a `/finance/calculate` endpoint that was removed from the
  FinCompass rewrite) and is not related to auth.
