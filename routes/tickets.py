from flask import Blueprint, render_template, redirect, url_for, flash, session, abort, request
from datetime import date

from forms import TicketForm
from mailer import Mailer
from models.ticket import Ticket
from models.user import User
from routes.announcements import admin_required
from routes.auth import login_required

tickets_bp = Blueprint("tickets", __name__, url_prefix="/tickets")


def can_manage_ticket(ticket):
    """Admins can manage every ticket; residents can manage only their own."""
    return session.get("role") == "admin" or ticket.user_id == session.get("user_id")


def save_report_and_notify(user, report):
    ticket = Ticket.create(user.id, report["category"], report["subject"], report["description"], report.get("incident_location"), report.get("incident_date"))
    sent_to_office = Mailer.send_ticket_to_municipality(ticket, user)
    confirmation_sent = Mailer.send_confirmation(ticket, user)
    if sent_to_office and confirmation_sent:
        flash(f"Your concern was submitted as ticket #{ticket.id}. We emailed you a confirmation.", "success")
    elif not confirmation_sent:
        flash(f"Ticket #{ticket.id} was saved, but we could not email your confirmation. Please check your email settings.", "warning")
    elif sent_to_office:
        flash(f"Ticket #{ticket.id} was emailed to the barangay, but your confirmation email could not be delivered.", "warning")
    else:
        flash(f"Ticket #{ticket.id} was saved and your confirmation was emailed, but the barangay email could not be delivered.", "warning")
    return ticket


@tickets_bp.route("/")
@login_required
def list_tickets():
    session.pop("pending_report", None)
    session.pop("pending_candidate_ids", None)
    if session.get("role") == "admin":
        tickets = Ticket.get_all()
    else:
        tickets = Ticket.get_by_user(session["user_id"])
        for ticket in tickets:
            ticket.is_owner = ticket.user_id == session["user_id"]
    return render_template("tickets/list.html", tickets=tickets, statuses=Ticket.STATUSES)


@tickets_bp.route("/new", methods=["GET", "POST"])
@login_required
def create_ticket():
    form = TicketForm()
    form.category.choices = [(c, c) for c in Ticket.CATEGORIES]

    pending = session.get("pending_report")
    if request.method == "GET" and pending:
        form.category.data = pending.get("category")
        form.subject.data = pending.get("subject")
        form.description.data = pending.get("description")
        form.incident_location.data = pending.get("incident_location")
        raw_date = pending.get("incident_date")
        form.incident_date.data = date.fromisoformat(raw_date) if raw_date else None

    if form.validate_on_submit():
        user = User.find_by_id(session["user_id"])
        if user is None:
            session.clear()
            return redirect(url_for("auth.login"))

        report = {
            "category": form.category.data,
            "subject": form.subject.data.strip(),
            "description": form.description.data.strip(),
            "incident_location": (form.incident_location.data or "").strip() or None,
            "incident_date": form.incident_date.data,
        }
        candidates = Ticket.find_similar_open(**report)
        if candidates:
            session["pending_report"] = {**report, "incident_date": report["incident_date"].isoformat() if report["incident_date"] else None}
            session["pending_candidate_ids"] = [ticket.id for ticket in candidates]
            return render_template(
                "tickets/duplicate_review.html", pending_report=report, candidates=candidates
            )

        session.pop("pending_report", None)
        session.pop("pending_candidate_ids", None)
        save_report_and_notify(user, report)
        return redirect(url_for("tickets.list_tickets"))

    return render_template("tickets/form.html", form=form, ticket=None)


@tickets_bp.route("/new/review", methods=["POST"])
@login_required
def resolve_duplicate_choice():
    report = session.get("pending_report")
    user = User.find_by_id(session.get("user_id"))
    if not report or not user:
        session.pop("pending_report", None)
        session.pop("pending_candidate_ids", None)
        flash("Your draft expired. Please enter the concern again.", "warning")
        return redirect(url_for("tickets.create_ticket"))
    report["incident_date"] = date.fromisoformat(report["incident_date"]) if report.get("incident_date") else None

    choice = request.form.get("choice")
    if choice == "separate":
        session.pop("pending_report", None)
        session.pop("pending_candidate_ids", None)
        save_report_and_notify(user, report)
        return redirect(url_for("tickets.list_tickets"))

    if choice == "support":
        try:
            ticket_id = int(request.form.get("ticket_id", ""))
        except (TypeError, ValueError):
            ticket_id = None
        allowed_ids = session.get("pending_candidate_ids", [])
        if ticket_id not in allowed_ids:
            abort(400)

        ticket = Ticket.get_by_id(ticket_id)
        valid_matches = Ticket.find_similar_open(**report)
        if ticket is None or ticket.status not in ("open", "in_progress") or all(
            match.id != ticket_id for match in valid_matches
        ):
            flash("That report is no longer open for support. Please review the matches again.", "info")
            return redirect(url_for("tickets.create_ticket"))

        if ticket.user_id == user.id:
            flash(f"You already submitted this concern as ticket #{ticket.id}. You can edit that ticket instead.", "info")
            session.pop("pending_report", None)
            session.pop("pending_candidate_ids", None)
            return redirect(url_for("tickets.edit_ticket", ticket_id=ticket.id))

        session.pop("pending_report", None)
        session.pop("pending_candidate_ids", None)
        if ticket.add_endorsement(user.id):
            confirmation_sent = Mailer.send_duplicate_confirmation(ticket, user)
            if confirmation_sent:
                flash(f"Your report was added as support for ticket #{ticket.id}. We emailed you a confirmation.", "success")
            else:
                flash(f"Your report was added as support for ticket #{ticket.id}, but its confirmation email could not be delivered.", "warning")
        else:
            flash(f"Your support is already counted for ticket #{ticket.id}. No duplicate was created.", "info")
        return redirect(url_for("tickets.list_tickets"))

    abort(400)


@tickets_bp.route("/<int:ticket_id>/edit", methods=["GET", "POST"])
@login_required
def edit_ticket(ticket_id):
    ticket = Ticket.get_by_id(ticket_id)
    if ticket is None:
        abort(404)
    # Resident reports stay as case records for the barangay to act on.
    if session.get("role") != "admin" and ticket.user_id != session.get("user_id"):
        flash("You can only edit your own reports.", "danger")
        return redirect(url_for("tickets.list_tickets"))
    if session.get("role") != "admin" and ticket.status != "open":
        flash("Only open tickets can be edited. Contact the barangay office if this ticket needs a correction.", "warning")
        return redirect(url_for("tickets.list_tickets"))

    form = TicketForm(obj=ticket)
    form.category.choices = [(c, c) for c in Ticket.CATEGORIES]
    if form.validate_on_submit():
        ticket.update_details(
            form.category.data,
            form.subject.data.strip(),
            form.description.data.strip(),
            (form.incident_location.data or "").strip() or None,
            form.incident_date.data,
        )
        reporter = User.find_by_id(ticket.user_id)
        sent = Mailer.send_ticket_update(ticket, reporter)
        if sent:
            flash(f"Ticket #{ticket.id} was updated and the municipality was notified.", "success")
        else:
            flash(f"Ticket #{ticket.id} was updated, but the municipality email could not be sent.", "warning")
        return redirect(url_for("tickets.list_tickets"))

    return render_template("tickets/form.html", form=form, ticket=ticket)


@tickets_bp.route("/<int:ticket_id>/delete", methods=["POST"])
@login_required
def delete_ticket(ticket_id):
    ticket = Ticket.get_by_id(ticket_id)
    if ticket is None:
        abort(404)
    if session.get("role") == "admin" or ticket.user_id != session.get("user_id"):
        flash("You can only manage your own tickets.", "danger")
        return redirect(url_for("tickets.list_tickets"))

    ticket.delete()
    flash(f"Ticket #{ticket.id} was deleted from CommunityBoard.", "info")
    return redirect(url_for("tickets.list_tickets"))


@tickets_bp.route("/<int:ticket_id>/status", methods=["POST"])
@login_required
@admin_required
def update_ticket_status(ticket_id):
    ticket = Ticket.get_by_id(ticket_id)
    if ticket is None:
        abort(404)

    new_status = request.form.get("status", "")
    if new_status not in Ticket.STATUSES:
        flash("That status is not valid.", "danger")
    else:
        raw_note = (request.form.get("resolution_note") or "").strip()
        if len(raw_note) > 300:
            flash("Resolution notes must be 300 characters or fewer.", "warning")
            return redirect(url_for("tickets.list_tickets"))
        resolution_note = raw_note or None
        if new_status == "resolved" and not resolution_note:
            flash("Add a short resolution note before marking a report resolved.", "warning")
        else:
            ticket.update_status(new_status, resolution_note)
            reporter = User.find_by_id(ticket.user_id)
            Mailer.send_ticket_status_update(ticket, reporter)
            flash(f"Ticket #{ticket.id} marked {new_status.replace('_', ' ')}.", "success")
    return redirect(url_for("tickets.list_tickets"))


