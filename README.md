# Restaurant Queue Management System

A production-ready restaurant queue and crowd management system built with Django REST Framework, MySQL, and React. Customers join a virtual queue, track their position in real-time, and get notified when their table is ready — no physical waiting in line.

---

## Problem It Solves

Restaurants face crowd congestion at peak hours. Customers don't know:
- How long they will wait
- What their position is
- When their turn is coming

This system solves all of that with a smart virtual queue.

---

## Features

- Customer joins queue by scanning QR code at entrance
- Token generation (T-001, T-002...) — resets daily
- Smart table allocation using best-fit algorithm
- Separate queues by party size (small / medium / large)
- Real-time queue position and wait time estimation
- Auto table assignment when a table becomes available
- Staff dashboard to view and manage queue
- Active tables panel — see who is seated where
- Customer can leave queue from their phone
- Staff can call next customer with one tap
- Staff can clear a table with one tap — next customer auto-called
- Auto no-show detection — if called customer doesn't arrive in 10 minutes, marked as no-show automatically
- Wait time recalculates for everyone after every queue change
- Background task processing with Celery + Redis
- Full visit history and analytics data
- Dark / light mode UI
- JWT authentication with OTP email verification
- Refresh token rotation with server-side blacklisting

---

## Tech Stack

### Backend

| Technology | Purpose |
|---|---|
| Python 3.10 | Programming language |
| Django 5.2 | Web framework |
| Django REST Framework | API development |
| MySQL 8.0 | Database |
| Redis | Message broker for Celery |
| Celery | Background task processing |
| Django Celery Beat | Periodic task scheduling |
| djangorestframework-simplejwt | JWT authentication + token blacklist |
| python-decouple | Environment variable management |
| Twilio | SMS notifications (optional) |

### Frontend

| Technology | Purpose |
|---|---|
| React 19 | UI framework |
| React Router v7 | Client-side routing |
| Axios | HTTP client with JWT refresh interceptor |
| react-icons | Icon library |
| CSS Custom Properties | Theme system — dark/light mode via `data-theme` attribute |
| ThemeContext | Dark/light mode state, persisted to `localStorage` |
| AuthContext | User auth state, JWT storage, async logout with token blacklist |

---

## Project Locations

```
~/Desktop/new_django_project/    ← Django backend (source of truth)
~/Desktop/restaurant-frontend/   ← React frontend (source of truth)
```

> The old frontend at `~/Desktop/new_django_project/frontend/customer_backup/` is archived and can be deleted once the active frontend has been smoke-tested.

---

## Project Structure

### Backend (`~/Desktop/new_django_project/`)

```
├── config/
│   ├── settings.py        ← All configuration
│   ├── urls.py            ← Main URL routing
│   └── celery.py          ← Celery setup
│
├── accounts/              ← Auth: User, OTPCode, JWT
├── restaurants/           ← Restaurant + TableUnit models
├── queue_manager/         ← Core queue logic
│   ├── models.py          ← Customer, QueueEntry, TableAssignment
│   ├── views.py           ← API views
│   ├── serializers.py     ← Data validation
│   ├── services.py        ← Business logic
│   ├── tasks.py           ← Celery background tasks
│   └── urls.py            ← Queue API URLs
├── orders/                ← Menu + Order management
├── notifications/         ← SMS logs + Feedback
│
├── .env                   ← Secret keys (not committed)
├── .env.example           ← Template for .env
├── requirements.txt       ← All dependencies
└── manage.py
```

### Frontend (`~/Desktop/restaurant-frontend/`)

```
src/
├── api/
│   └── axios.js           ← Axios instance + JWT interceptors + all API methods
├── context/
│   ├── AuthContext.js     ← User state, login, logout (with token blacklist)
│   └── ThemeContext.js    ← Dark/light mode state, persisted to localStorage
├── components/
│   ├── layout/
│   │   └── PageWrapper.js ← Framer Motion page transition wrapper
│   └── ui/
│       ├── Button.js      ← Reusable button component
│       ├── Input.js       ← Reusable input with icon + error support
│       ├── ThemeToggle.js ← Dark/light mode toggle button
│       └── Toast.js       ← Toast notification system
├── pages/
│   ├── auth/
│   │   ├── Login.js       ← Email/password login
│   │   ├── Register.js    ← Admin + customer registration (role toggle)
│   │   └── VerifyOTP.js   ← 6-digit OTP verification with countdown
│   ├── customer/
│   │   ├── CustomerHome.js  ← Dashboard: restaurant info + join CTA
│   │   ├── JoinQueue.js     ← Visual party size selector + join flow
│   │   └── QueueStatus.js   ← Live queue position, all states, leave queue
│   └── admin/
│       └── AdminDashboard.js ← Waiting queue + active tables + call/clear
├── utils/
│   └── constants.js       ← RESTAURANT_ID, STATUS_LABELS, QUEUE_TYPES
└── styles/
    └── theme.css          ← CSS custom properties for dark/light tokens
```

---

## Frontend Routes

| Route | Access | Description |
|---|---|---|
| `/` | Public | Landing page |
| `/login` | Public | Login with email + password |
| `/register` | Public | Register as admin or customer |
| `/verify-otp` | Public | OTP email verification |
| `/customer/home` | Customer only | Dashboard + join queue CTA |
| `/customer/join` | Customer only | Join queue — party size selector |
| `/customer/status` | Customer only | Live queue position tracking |
| `/admin/dashboard` | Admin only | Queue management + active tables |

---

## localStorage Keys

| Key | Set by | Contains |
|---|---|---|
| `accessToken` | `AuthContext.login` | JWT access token (12h lifetime) |
| `refreshToken` | `AuthContext.login` | JWT refresh token (7d lifetime, rotated) |
| `user` | `AuthContext.login` | JSON object: `{id, email, name, role, restaurant_id, restaurant_name}` |
| `queueToken` | `JoinQueue.js` | Queue token string (e.g. `T-001`) — cleared on leave/completion |
| `theme` | `ThemeContext` | `"dark"` or `"light"` — persists across sessions |
| `pendingEmail` | `Register.js` / `Login.js` | Email address passed to OTP verification page |
| `pendingRole` | `Register.js` | Role passed to OTP page (`"admin"` or `"customer"`) |

---

## API Endpoints

### Auth (`/api/auth/`)

| Method | URL | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/admin/register/` | Public | Admin registration |
| POST | `/api/auth/customer/register/` | Public | Customer registration |
| POST | `/api/auth/verify-otp/` | Public | OTP email verification |
| POST | `/api/auth/login/` | Public | Login → returns JWT tokens |
| POST | `/api/auth/resend-otp/` | Public | Resend OTP |
| POST | `/api/auth/token/refresh/` | Refresh token | Rotate access token |
| POST | `/api/auth/token/blacklist/` | Refresh token | Invalidate refresh token (logout) |
| GET | `/api/auth/profile/` | JWT | Get current user profile |

### Queue (`/api/queue/`)

| Method | URL | Auth | Description |
|---|---|---|---|
| POST | `/api/queue/join-queue/` | Public | Customer joins queue |
| GET | `/api/queue/queue-status/<token>/` | Public | Check queue position |
| POST | `/api/queue/leave-queue/` | Public | Customer leaves queue |
| GET | `/api/queue/restaurant-queue/<id>/` | Admin | View waiting queue |
| GET | `/api/queue/staff-dashboard/<id>/` | Admin | Waiting queue + active tables |
| POST | `/api/queue/call-customer/` | Admin | Call next customer |
| POST | `/api/queue/clear-table/` | Admin | Clear table → auto-call next |

### Orders (`/api/orders/`)

| Method | URL | Auth | Description |
|---|---|---|---|
| GET | `/api/orders/menu/<id>/` | Public | Get restaurant menu |
| POST | `/api/orders/create/` | Admin | Create order for table |
| PATCH | `/api/orders/<id>/status/` | Admin | Update order status |
| GET | `/api/orders/restaurant/<id>/active/` | Admin | Active orders (kitchen view) |

---

## Database Design

```
Restaurant
    ├── TableUnit (many tables per restaurant)
    │       └── TableAssignment (history of who sat where)
    ├── QueueEntry (customer queue history)
    │       ├── TableAssignment
    │       ├── NotificationLog
    │       └── Feedback
    └── MenuItem
            └── OrderItem → OrderRecord
```

---

## Installation & Startup

### Backend Setup

```bash
# 1. Navigate to backend
cd ~/Desktop/new_django_project

# 2. Activate virtual environment
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create MySQL database
mysql -u root -p
CREATE DATABASE restaurant_queue_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'queue_user'@'localhost' IDENTIFIED BY 'YourPassword';
GRANT ALL PRIVILEGES ON restaurant_queue_db.* TO 'queue_user'@'localhost';
FLUSH PRIVILEGES;

# 5. Create .env file (copy from .env.example and fill in values)
cp .env.example .env

# 6. Run migrations
python manage.py migrate

# 7. (Optional) Seed test data
python manage.py seed_data

# 8. Create superuser
python manage.py createsuperuser

# 9. Start server
python manage.py runserver
```

### Frontend Setup

```bash
# 1. Navigate to frontend
cd ~/Desktop/restaurant-frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm start

# 4. Build for production
npm run build
```

### Running Background Tasks

Open 3 separate terminals:

**Terminal 1 — Django server:**
```bash
cd ~/Desktop/new_django_project && source venv/bin/activate
python manage.py runserver
```

**Terminal 2 — Celery worker:**
```bash
cd ~/Desktop/new_django_project && source venv/bin/activate
celery -A config worker --loglevel=info
```

**Terminal 3 — Celery beat (scheduler):**
```bash
cd ~/Desktop/new_django_project && source venv/bin/activate
celery -A config beat --loglevel=info
```

---

## Authentication Flow

```
Register (admin or customer)
    ↓
OTP sent to email
    ↓
Verify OTP → account activated
    [Admin only: Restaurant + 8 default tables auto-created]
    ↓
Login → JWT access token (12h) + refresh token (7d)
    ↓
Tokens stored in localStorage
    ↓
On 401 → auto-refresh once → retry request
    ↓
On logout → POST /api/auth/token/blacklist/ → clear localStorage
```

---

## Queue Flow

```
Customer arrives at restaurant
        ↓
Opens app → Customer Home page
        ↓
Taps "Join Queue" → selects party size
        ↓
System checks: is a table available?

YES → Assign table immediately
      Token shown, status = "seated"

NO  → Add to virtual queue
      Give token (T-001)
      Show estimated wait time
      Customer waits anywhere
        ↓
Staff sees queue on tablet dashboard
        ↓
Staff taps "Call" → customer status = "called"
Customer has 10 minutes to arrive
        ↓
ARRIVES     → Staff taps "Clear Table" when done
NO-SHOW     → Celery auto-detects after 10 min
               Status = "no_show", table freed
        ↓
Table cleared → next waiting customer auto-called
Everyone's wait time recalculated
```

---

## Queue Logic

### Separate Queues by Party Size
```
Small  (1-2 people) → compete for 2-seater tables only
Medium (3-4 people) → compete for 4-seater tables only
Large  (5+ people)  → compete for 6-seater tables only
```

### Wait Time Formula
```
rounds = ceil(people_ahead / occupied_tables)
wait_time = rounds × average_meal_duration
```

### Best-Fit Table Allocation
```
Party of 3 arrives
Available: 2-seater, 4-seater, 6-seater
System picks: 4-seater (smallest that fits)
Saves 6-seater for larger parties
```

---

## Future Improvements

- QR code generation per restaurant (encode restaurant_id in URL)
- WebSocket real-time updates (replace polling)
- SMS notifications via Twilio
- Analytics dashboard (peak hours, no-show rate, avg wait trends)
- Password reset flow
- Table management UI (add/remove/edit tables)
- Restaurant profile editing
- Mobile app

---

## Author

**Rohit Yadav**

GitHub: [https://github.com/rohit2002yadav](https://github.com/rohit2002yadav)

---

## License

This project is developed for educational purposes.
