# Demo Script — 5 to 10 Minute Walkthrough

Use this for technical interviews, portfolio presentations, or recorded demos.
Estimated time per section is noted. Total: ~8 minutes at a comfortable pace.

---

## 1. Opening — Problem Statement (45 seconds)

> "Imagine it's Saturday evening and you walk into a busy restaurant. There's a crowd at the entrance, no one knows how long the wait is, and the host is juggling a paper list. That's the problem this project solves."

> "I built a virtual queue management system. Customers join from their phone, see their live position and estimated wait time, and get called when their table is ready — no physical line, no guessing."

---

## 2. Tech Stack (30 seconds)

> "The backend is Django REST Framework with MySQL as the database and Redis + Celery for background tasks. The frontend is React 19 with a custom JWT refresh interceptor. Authentication uses JWT with OTP email verification."

Point to the architecture diagram in the README if screen-sharing.

---

## 3. Architecture (1 minute)

> "The system has five Django apps:"

- `accounts` — user registration, OTP verification, JWT login
- `restaurants` — restaurant and table models
- `queue_manager` — the core: all queue logic lives in `services.py`
- `orders` — menu and order management
- `notifications` — SMS logs and customer feedback

> "All business logic is in `services.py`, not in views. Views only handle HTTP — they validate the request, call a service function, and return the response. This keeps the logic testable and the views thin."

> "Every state-changing operation — joining, calling, seating, clearing — is wrapped in `@transaction.atomic` with `select_for_update` on the contested row. This prevents race conditions when two staff members tap 'Call' at the same time."

---

## 4. Customer Workflow — Live Demo (2 minutes)

Walk through these screens:

**Step 1 — Register**
> "A customer registers with their email. The system sends a 6-digit OTP generated with Python's `secrets` module — cryptographically secure, not `random`."

**Step 2 — Customer Home**
> "After login, the customer sees their restaurant and a 'Join Queue' button."

**Step 3 — Join Queue**
> "They select their party size. The system immediately checks if a matching table is available."
> "If yes — they're seated instantly, no queue. If no — they get a token like T-001 and see their position and estimated wait time."

**Step 4 — Queue Status**
> "This page polls every few seconds. It shows position, estimated wait, and status. When called, it shows a 'Please proceed to the host' message. When seated, it shows a note that their order is being taken. When completed, a feedback button appears."

---

## 5. Admin Workflow — Live Demo (2 minutes)

Walk through the Admin Dashboard:

**Waiting Queue panel (left side)**
> "The staff sees all waiting customers — their token, party size, and how long they've been waiting. They tap 'Call' to call the next customer."

**Active Tables panel (right side)**
> "Each table card shows who is seated, their token, and party size. The badge colour tells the story — orange means 'called, not yet seated', green means 'seated'."
> "When a customer arrives, staff tap 'Seat'. When the visit is done, staff tap 'Clear' — the table is freed and the next waiting customer is automatically called."

---

## 6. Queue Lifecycle (1 minute)

Draw or point to the lifecycle diagram:

```
waiting → called → seated → completed
                ↘
              no_show (auto, after 10 min)
```

> "The no-show detection is a Celery periodic task that runs every minute. If a called customer hasn't been seated within 10 minutes, it marks them as no-show, frees the table, and auto-calls the next waiting customer. No staff action needed."

> "There's also an immediate-seating path — if a table is available when the customer joins, they go straight to 'seated', skipping 'called' entirely. The frontend detects this by checking whether `called_at` is null."

---

## 7. Challenges Solved (1 minute)

**Race conditions:**
> "What happens if two staff members tap 'Call' at the same time? Without protection, you'd assign the same table twice. I solved this with `select_for_update` inside `@transaction.atomic`. The second request hits a locked row, reads the already-updated status, and returns a 400 — 'no waiting customers'. The database enforces it, not application-level checks."

**Best-fit allocation:**
> "A party of 3 shouldn't take a 6-seater when a 4-seater is free. The allocation function sorts available tables by capacity and picks the smallest one that fits the party. This maximises the number of parties the restaurant can seat simultaneously."

**Wait time estimation:**
> "Wait time isn't just 'position × average meal time'. It accounts for how many tables of the right size are occupied. If 3 tables are occupied and 6 people are ahead of you, that's 2 rounds, not 6."

---

## 8. Security (30 seconds)

> "A few security decisions worth calling out:"
- OTP uses `secrets.randbelow` — not `random`, which is not cryptographically secure
- JWT refresh tokens are blacklisted server-side on logout — clearing localStorage alone isn't enough
- CORS is configurable via `.env` — `CORS_ALLOW_ALL_ORIGINS=False` in production with an explicit allowed origins list
- Admin endpoints check both JWT validity and that the requesting user owns the restaurant they're querying

---

## 9. Testing (30 seconds)

> "The project has 40 automated tests. They cover the full queue lifecycle — join, call, seat, clear, leave, no-show. They also test the race condition scenarios directly: calling a customer twice, seating a non-called entry, clearing an already-cleared table. All 40 pass."

```bash
python manage.py test
# 40 tests, 0 failures, 0 errors
```

---

## 10. Future Improvements (30 seconds)

> "The infrastructure for SMS is already in place — Twilio is integrated, it just needs `SMS_ENABLED=True` in `.env`. The next meaningful upgrade would be WebSockets to replace polling on the queue status page. I'd also add a QR code generator so each restaurant gets a unique scan-to-join URL."

---

## Closing

> "The thing I'm most proud of here is that the core logic — the queue, the allocation, the lifecycle — is all in one file, `services.py`, with no business logic leaking into views or models. It made testing straightforward and the code easy to reason about."

---

## Tips for the Demo

- Have the app running locally before you start
- Open two browser windows side by side: customer view (left) and admin dashboard (right)
- Use incognito for the customer window so sessions don't conflict
- Seed the database with `python manage.py seed_data` so there are tables and a restaurant ready
- Have the README open in a third tab for the architecture diagram
