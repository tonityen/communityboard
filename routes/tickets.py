from flask import Blueprint, render_template, redirect, url_for, flash, session, abort, request

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


@tickets_bp.route("/")
@login_required
def list_tickets():
    if session.get("role") == "admin":
        tickets = Ticket.get_all()
    else:
        tickets = Ticket.get_by_user(session["user_id"])
    return render_template("tickets/list.html", tickets=tickets, statuses=Ticket.STATUSES)


@tickets_bp.route("/new", methods=["GET", "POST"])
@login_required
def create_ticket():
    form = TicketForm()
    form.category.choices = [(c, c) for c in Ticket.CATEGORIES]

    if form.validate_on_submit():
        user = User.find_by_id(session["user_id"])
        if user is None:
            session.clear()
            return redirect(url_for("auth.login"))

        ticket = Ticket.create(
            user.id, form.category.data, form.subject.data.strip(), form.description.data.strip()
        )
        sent = Mailer.send_ticket_to_municipality(ticket, user)
        Mailer.send_confirmation(ticket, user)

        if sent:
            flash("Your ticket was sent to the municipality. Check your email for a confirmation.", "success")
        else:
            flash("Your ticket was saved, but the email could not be sent right now. Please try again later.", "warning")
        return redirect(url_for("tickets.list_tickets"))

    return render_template("tickets/form.html", form=form, ticket=None)


@tickets_bp.route("/<int:ticket_id>/edit", methods=["GET", "POST"])
@login_required
def edit_ticket(ticket_id):
    ticket = Ticket.get_by_id(ticket_id)
    if ticket is None:
        abort(404)
    if not can_manage_ticket(ticket):
        flash("You can only manage your own tickets.", "danger")
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
    if not can_manage_ticket(ticket):
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
        ticket.update_status(new_status)
        flash(f"Ticket #{ticket.id} updated.", "success")
    return redirect(url_for("tickets.list_tickets"))


