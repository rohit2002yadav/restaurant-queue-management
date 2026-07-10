# Screenshot Guide

These are the screenshots you should capture and add to `docs/screenshots/` for the README.

---

## Required Screenshots

### 1. `join-queue.png` — Customer: Party Size Selector
**Page:** `/customer/join`
**What to show:**
- The visual party size selector (1–2, 3–4, 5+ buttons)
- One option selected/highlighted
- The "Join Queue" button visible
- Dark mode preferred (shows off the theme)

**Tip:** Select "Medium (3–4)" so the button state is visible.

---

### 2. `queue-status.png` — Customer: Live Queue Position
**Page:** `/customer/status`
**What to show:**
- Token displayed prominently (e.g. T-003)
- Queue position (e.g. "Position 2 of 5")
- Estimated wait time (e.g. "~12 minutes")
- Status badge ("Waiting" or "Called")
- "Leave Queue" button visible

**Tip:** Have 3–4 people in the queue so the position number is meaningful.

---

### 3. `admin-dashboard.png` — Admin: Staff Dashboard
**Page:** `/admin/dashboard`
**What to show:**
- Both panels visible: "Waiting Queue" (left) and "Active Tables" (right)
- At least 2–3 entries in the waiting queue
- At least 2 active table cards — one with orange "Called" badge, one with green "Seated" badge
- "Call", "Seat", and "Clear" buttons visible

**Tip:** This is your most important screenshot. Make it wide (1400px+) so both panels are visible.

---

### 4. `login.png` — Login Page
**Page:** `/login`
**What to show:**
- Email and password fields
- Login button
- Link to register
- Dark or light mode (your choice — pick whichever looks better)

---

### 5. `register.png` — Registration Page
**Page:** `/register`
**What to show:**
- The role toggle (Admin / Customer) — have "Admin" selected
- All form fields visible
- The form looking clean and complete

---

### 6. `otp.png` — OTP Verification
**Page:** `/verify-otp`
**What to show:**
- The 6-digit OTP input
- The countdown timer
- "Resend OTP" link
- The email address shown (use a placeholder like `user@example.com`)

---

## Optional (Nice to Have)

### 7. `customer-home.png` — Customer Home
**Page:** `/customer/home`
- Restaurant name and info
- "Join Queue" CTA button

### 8. `queue-status-called.png` — Customer: Called State
**Page:** `/customer/status` with status = "called"
- "You've been called!" message
- Instruction to proceed to host
- Different visual state from "waiting"

### 9. `queue-status-seated.png` — Customer: Seated State
- "You're seated!" message
- Feedback note visible

### 10. `dark-light-comparison.png` — Theme Toggle
- Side-by-side or split-screen of dark vs light mode on the same page
- Shows off the theme system

---

## Screenshot Tips

- Use a browser width of **1440px** for desktop screenshots
- Use **1080px** height for a clean 4:3 ratio
- Use browser DevTools device emulation at **390px width** for mobile screenshots
- Capture with the browser chrome hidden (full-screen or use a screenshot extension)
- Tools: Lightshot, Greenshot, or browser built-in (`Cmd+Shift+4` on Mac, `PrtSc` on Linux)
- Compress images before committing: use [squoosh.app](https://squoosh.app) or `imagemagick`

```bash
# Resize and compress with ImageMagick (optional)
convert admin-dashboard.png -resize 1440x -quality 85 admin-dashboard.png
```
