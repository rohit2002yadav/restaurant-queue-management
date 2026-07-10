# Resume — Project Summary

Copy one of the versions below depending on your resume format.

---

## Version A — Bullet points (most common format)

**Restaurant Queue Management System** | Python, Django REST Framework, React, MySQL, Redis, Celery
*[github.com/rohit2002yadav/restaurant-queue-system](https://github.com/rohit2002yadav)*

- Built a full-stack virtual queue system replacing physical restaurant lines; customers join, track position, and get called via a React SPA backed by a Django REST API
- Designed a best-fit table allocation algorithm that matches party size to the smallest available table, maximising restaurant throughput
- Implemented concurrent-safe state transitions using `@transaction.atomic` + `select_for_update`, preventing double-call and double-seat race conditions
- Automated no-show detection with a Celery periodic task that frees tables and auto-calls the next customer after a 10-minute timeout
- Secured the API with JWT authentication, OTP email verification (CSPRNG), and server-side refresh token blacklisting
- Achieved 40/40 passing tests covering the full queue lifecycle, race conditions, and authentication flows

---

## Version B — Single-line summary (for space-constrained resumes)

**Restaurant Queue Management System** — Full-stack virtual queue system (Django REST Framework + React 19 + MySQL + Celery) with best-fit table allocation, JWT + OTP auth, concurrent-safe state transitions, and automated no-show detection. 40 tests passing.

---

## Version C — Two-line narrative (for "Projects" sections with descriptions)

Designed and built a production-ready restaurant queue management system from scratch. The backend (Django REST Framework, MySQL, Celery/Redis) handles concurrent table allocation using a best-fit algorithm with atomic database transactions. The React 19 frontend provides separate customer and admin flows with JWT authentication, OTP verification, dark/light theming, and a real-time staff dashboard.
