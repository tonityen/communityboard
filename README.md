# CommunityBoard - Local Community Bulletin System

Web system for Barangay Duhat, Santa Cruz, Laguna (Flask + MySQL + Bootstrap).

## Setup (Windows)

1. Create and activate a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
2. Install packages:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your MySQL password and a secret key.
4. Create the database: open `schema.sql` in MySQL Workbench and run it.
5. Run the app:
   ```
   python app.py
   ```
6. Open http://127.0.0.1:5000

## Make an admin account

Register normally, then run this in MySQL:
```
UPDATE users SET role = 'admin' WHERE email = 'your-email@example.com';
```
## Ticket workflow

Residents can submit concerns, edit their own tickets while they are open, and delete their own tickets. Admins can review all tickets, edit or delete them, and update their status. Editing a ticket sends the updated details to the municipality or barangay by email.
## Email verification and reports

New accounts receive a six-digit email verification code. Codes expire after 10 minutes, and a new code can be requested once per minute. Verification happens on the CommunityBoard page; no tunnel URL is embedded in the verification email.

Concern reports are limited to an 8–100 character title and a 30–600 character description. When a recent open report in the same category has similar wording, residents can add support to that ticket or submit a separate report. Support counts are shown on the ticket list. New reports still email the configured barangay contact and send a confirmation to the resident.

Reports can include an approximate incident date and location to improve duplicate matching. Admins can move reports through open, in progress, and resolved; a short resolution note is required to mark a report resolved and is emailed to its reporter. Residents can view the status progress and barangay update. Announcements and events have categories, search, and category filters; events can also be filtered by upcoming or past.

## Local network access

Run CommunityBoard on the computer that hosts it. A phone can open the computer's local network address on the same Wi-Fi. Access from a different network requires a deployed public HTTPS host; a localhost address only works on the computer itself. Set `SESSION_COOKIE_SECURE=true` only when the deployed site uses HTTPS.

