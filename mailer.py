import smtplib
from email.message import EmailMessage

from flask import current_app, url_for
from tokens import TokenService


class Mailer:

    @staticmethod
    def send(to_address, subject, body, reply_to=None):
        """Send one email. Returns True if sent, False if something went wrong."""
        config = current_app.config
        if not config["MAIL_USERNAME"] or not config["MAIL_PASSWORD"] or not to_address:
            current_app.logger.warning("Email is not set up in the .env file.")
            return False

        message = EmailMessage()
        message["From"] = config["MAIL_USERNAME"]
        message["To"] = to_address
        message["Subject"] = subject.replace("\r", " ").replace("\n", " ")
        if reply_to:
            message["Reply-To"] = reply_to
        message.set_content(body)

        try:
            with smtplib.SMTP(config["MAIL_SERVER"], config["MAIL_PORT"], timeout=15) as server:
                server.starttls()
                server.login(config["MAIL_USERNAME"], config["MAIL_PASSWORD"])
                server.send_message(message)
            return True
        except (smtplib.SMTPException, OSError, ValueError) as error:
            current_app.logger.error(f"Email failed: {error}")
            return False

    @staticmethod
    def send_ticket_to_municipality(ticket, user):
        body = (
            "A resident submitted a concern through CommunityBoard (Barangay Duhat).\n\n"
            f"Ticket number: {ticket.id}\n"
            f"Category: {ticket.category}\n"
            f"Subject: {ticket.subject}\n"
            f"Submitted by: {user.full_name} ({user.email})\n\n"
            "Description:\n"
            f"{ticket.description}\n"
        )
        return Mailer.send(
            current_app.config["MUNICIPALITY_EMAIL"],
            f"[CommunityBoard Ticket #{ticket.id}] {ticket.subject}",
            body,
            reply_to=user.email,
        )

    @staticmethod
    def send_ticket_update(ticket, user):
        body = (
            "A resident updated a concern through CommunityBoard (Barangay Duhat).\n\n"
            f"Ticket number: {ticket.id}\n"
            f"Category: {ticket.category}\n"
            f"Subject: {ticket.subject}\n"
            f"Submitted by: {user.full_name} ({user.email})\n\n"
            "Updated description:\n"
            f"{ticket.description}\n"
        )
        return Mailer.send(
            current_app.config["MUNICIPALITY_EMAIL"],
            f"[CommunityBoard Ticket #{ticket.id} Updated] {ticket.subject}",
            body,
            reply_to=user.email,
        )
    @staticmethod
    def send_confirmation(ticket, user):
        body = (
            f"Hello {user.full_name},\n\n"
            "We received your concern and sent it to the municipality of Santa Cruz.\n\n"
            f"Ticket number: {ticket.id}\n"
            f"Subject: {ticket.subject}\n\n"
            "You can check its status anytime on CommunityBoard under Tickets.\n"
        )
        return Mailer.send(user.email, f"We received your ticket #{ticket.id}", body)

    @staticmethod
    def public_url(endpoint, **values):
        """Build email links from the configured public address when available."""
        public_base = current_app.config.get("PUBLIC_BASE_URL", "")
        path = url_for(endpoint, **values)
        if public_base:
            return f"{public_base}{path}"
        values["_external"] = True
        return url_for(endpoint, **values)
    @staticmethod
    def send_verification(user):
        token = TokenService.make({"id": user.id, "email": user.email}, "verify-email")
        link = Mailer.public_url("verification.verify_email", token=token)
        body = (
            f"Hello {user.full_name},\n\n"
            "Thank you for registering on CommunityBoard (Barangay Duhat).\n"
            "Please click this link to verify your email. It only works for 24 hours:\n\n"
            f"{link}\n\n"
            "If you did not create this account, you can ignore this email.\n"
        )
        return Mailer.send(user.email, "Verify your CommunityBoard account", body)

    @staticmethod
    def send_password_reset(user):
        token = TokenService.make(
            {"id": user.id, "fp": user.password_fingerprint()}, "reset-password"
        )
        link = Mailer.public_url("password_reset.reset_password", token=token)
        body = (
            f"Hello {user.full_name},\n\n"
            "We received a request to reset your CommunityBoard password.\n"
            "Click this link to choose a new password. It works for 30 minutes and only once:\n\n"
            f"{link}\n\n"
            "If you did not ask for this, you can ignore this email. Your password will not change.\n"
        )
        return Mailer.send(user.email, "Reset your CommunityBoard password", body)


