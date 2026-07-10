# LinkedIn Project Description

Go to your LinkedIn profile → Add section → Projects → Add project.

---

**Project name:**
Restaurant Queue Management System

**Associated with:**
*(your university or current position)*

**Date:**
*(month/year you completed it)*

**Project URL:**
https://github.com/rohit2002yadav/restaurant-queue-system

---

**Description (paste this into the description field):**

---

Built a full-stack virtual queue management system that eliminates physical waiting lines at restaurants.

Customers scan a QR code, join a virtual queue from their phone, and receive a live position tracker with estimated wait time. Staff manage the queue from a real-time dashboard — calling customers, seating them, and clearing tables with a single tap.

**What I built:**

🔧 Backend — Django REST Framework + MySQL + Celery/Redis
• Best-fit table allocation algorithm (party of 3 gets a 4-seater, not a 6-seater)
• Separate queues per party size so small and large groups never compete for the same table
• Concurrent-safe state transitions using database-level locking (@transaction.atomic + select_for_update) — prevents double-call and double-seat under simultaneous requests
• Automated no-show detection via Celery periodic task — frees table and auto-calls next customer after 10 minutes
• JWT authentication with OTP email verification using a cryptographically secure random number generator
• Server-side refresh token blacklisting for secure logout

⚛️ Frontend — React 19 + Axios
• Separate customer and admin flows with role-based route protection
• JWT refresh interceptor — silently rotates tokens on 401, retries the original request
• Dark/light mode with localStorage persistence
• Real-time staff dashboard showing waiting queue and active tables simultaneously

✅ 40 automated tests covering the full queue lifecycle, race conditions, and authentication flows.

**Tech stack:** Python · Django · Django REST Framework · React 19 · MySQL · Redis · Celery · JWT · Twilio (SMS)

---

**Skills to tag:**
Python · Django · React.js · REST APIs · MySQL · Redis · Celery · JWT · Full-Stack Development · Software Engineering
