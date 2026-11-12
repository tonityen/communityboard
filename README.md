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
## Mobile access outside your Wi-Fi

For a temporary defense demo, install cloudflared, start CommunityBoard, then run cloudflared tunnel --url http://127.0.0.1:5000 in a second terminal. Open the generated HTTPS trycloudflare.com address on the phone. Both the app and tunnel must stay running. The temporary address changes when restarted, and anyone with the address can access the app.

For verification and password-reset emails, set PUBLIC_BASE_URL in .env to the generated HTTPS address, then restart CommunityBoard before registering or requesting a reset. Use demo data only for a temporary public tunnel.

