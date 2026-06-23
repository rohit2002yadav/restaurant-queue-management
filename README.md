# Restaurant Queue Management System

A production-ready restaurant queue and crowd management system built with Django REST Framework and MySQL. Customers scan a QR code at the entrance, join a virtual queue, and get notified when their table is ready — no physical waiting in line.

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
- Customer can leave queue from their phone
- Staff can call next customer with one tap
- Auto no-show detection — if called customer doesn't arrive in 10 minutes, marked as no-show automatically
- Wait time recalculates for everyone after every queue change
- Background task processing with Celery + Redis
- Full visit history and analytics data

---

## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.10 | Programming language |
| Django 5.2 | Web framework |
| Django REST Framework | API development |
| MySQL 8.0 | Database |
| Redis | Message broker for Celery |
| Celery | Background task processing |
| Django Celery Beat | Periodic task scheduling |
| python-decouple | Environment variable management |

---

## Project Structure

```
restaurant_queue/
├── config/
│   ├── settings.py        ← All configuration
│   ├── urls.py            ← Main URL routing
│   └── celery.py          ← Celery setup
│
├── restaurants/           ← Restaurant + Table models
│   ├── models.py
│   └── admin.py
│
├── queue_manager/         ← Core queue logic
│   ├── models.py          ← Customer, QueueEntry, TableAssignment
│   ├── views.py           ← API views
│   ├── serializers.py     ← Data validation
│   ├── services.py        ← Business logic
│   ├── tasks.py           ← Celery background tasks
│   └── urls.py            ← Queue API URLs
│
├── orders/                ← Menu + Order management
│   └── models.py
│
├── notifications/         ← SMS logs + Feedback
│   └── models.py
│
├── .env                   ← Secret keys (not uploaded)
├── requirements.txt       ← All dependencies
└── manage.py
```

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

## API Endpoints

| Method | URL | Description |
|---|---|---|
| POST | /api/queue/join-queue/ | Customer joins queue |
| GET | /api/queue/queue-status/\<token\>/ | Check queue position |
| GET | /api/queue/restaurant-queue/\<id\>/ | Staff views full queue |
| POST | /api/queue/clear-table/ | Staff clears table |
| POST | /api/queue/leave-queue/ | Customer leaves queue |
| POST | /api/queue/call-customer/ | Staff calls next customer |

---

## Installation Guide

### 1. Clone Repository

```bash
git clone https://github.com/rohit2002yadav/restaurant-queue-management.git
cd restaurant-queue-management
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create MySQL Database

```sql
CREATE DATABASE restaurant_queue_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'queue_user'@'localhost' IDENTIFIED BY 'YourPassword';
GRANT ALL PRIVILEGES ON restaurant_queue_db.* TO 'queue_user'@'localhost';
FLUSH PRIVILEGES;
```

### 5. Create .env File

```
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=restaurant_queue_db
DB_USER=queue_user
DB_PASSWORD=YourPassword
DB_HOST=localhost
DB_PORT=3306
```

### 6. Run Migrations

```bash
python manage.py migrate
```

### 7. Create Superuser

```bash
python manage.py createsuperuser
```

### 8. Run Development Server

```bash
python manage.py runserver
```

---

## Running Background Tasks

Open 3 separate terminals:

**Terminal 1 — Django server:**
```bash
python manage.py runserver
```

**Terminal 2 — Celery worker:**
```bash
celery -A config worker --loglevel=info
```

**Terminal 3 — Celery beat (scheduler):**
```bash
celery -A config beat --loglevel=info
```

---

## How It Works

```
Customer arrives at restaurant
        ↓
Scans QR code → opens webpage on phone
        ↓
Enters name, phone number, party size
        ↓
System checks: is a table available?

YES → Assign table immediately
      Customer goes directly to table

NO  → Add to virtual queue
      Give token number (T-001)
      Show estimated wait time
      Customer waits anywhere
        ↓
Staff sees queue on tablet dashboard
        ↓
Staff taps "Call" → customer notified
        ↓
Customer has 10 minutes to arrive

ARRIVES     → Staff seats them
DOESN'T COME → Auto marked as no-show
               Table freed automatically
               Next customer called
        ↓
Customer finishes meal
        ↓
Staff taps "Clear Table"
        ↓
Next waiting customer auto-seated
Everyone's wait time updated
```

---

## Queue Logic

### Separate Queues by Party Size
```
Small  (1-2 people) → compete for 2-seater tables only
Medium (3-4 people) → compete for 4-seater tables only
Large  (5+ people)  → compete for 6-seater tables only
```

This prevents a party of 6 from blocking a party of 2.

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

- SMS notifications via Twilio
- React frontend for customer phone page
- QR code generation for each restaurant
- WebSocket real-time updates
- Payment integration
- Machine learning for wait time prediction
- Multi-branch restaurant support
- Mobile app

---

## Author

**Rohit Yadav**

GitHub: [https://github.com/rohit2002yadav](https://github.com/rohit2002yadav)

---

## License

This project is developed for educational purposes.
