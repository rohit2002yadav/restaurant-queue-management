# Release Notes — v1.0.0

**Restaurant Queue Management System**
Initial public release.

---

## What's included

### Core queue system
- Virtual queue with token generation (T-001, T-002…)
- Best-fit table allocation — party of 3 gets a 4-seater, not a 6-seater
- Separate queues per party size (small / medium / large)
- Full status lifecycle: waiting → called → seated → completed
- Immediate seating when a table is available at join time
- Auto no-show detection via Celery periodic task (10-minute window)
- Auto-call next customer after table is cleared or no-show is detected
- Wait time recalculation after every queue change

### Staff dashboard
- Real-time view of waiting queue and active tables
- Call, Seat, and Clear actions with one tap
- Table management — add, edit, delete tables
- Order management — create orders per table, kitchen view

### Authentication
- JWT access tokens (12h) + refresh tokens (7d) with rotation
- Server-side refresh token blacklisting on logout
- OTP email verification using CSPRNG (`secrets` module)
- Password reset via OTP email

### Frontend
- Separate customer and admin flows with role-based route protection
- JWT refresh interceptor — silent token rotation on 401
- Dark / light mode with localStorage persistence
- Customer feedback form post-visit

### Infrastructure
- MySQL 8.0 with `@transaction.atomic` + `select_for_update` on all state writes
- Redis + Celery for background task processing
- All configuration via `.env` — no hardcoded secrets
- CORS, Redis URL, and SMS toggle all env-driven

### Testing
- 60 automated tests — all passing
- Coverage: full queue lifecycle, race conditions (double-call, double-seat, double-clear), OTP, JWT, wait time, best-fit allocation

---

## Tech stack

Python 3.10 · Django 5.2 · Django REST Framework 3.17 · React 19 · MySQL 8.0 · Redis 7.x · Celery 5.6 · JWT

---

## Setup

See [README.md](../README.md) for full installation instructions.
