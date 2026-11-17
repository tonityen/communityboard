from flask import Blueprint, render_template, session

from models.announcement import Announcement
from models.event import Event
from models.ticket import Ticket
from models.user import User
from routes.auth import login_required

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    show_welcome_modal = session.pop("show_welcome_modal", False)
    # Everyone sees the latest announcements and the next events.
    data = {
        "announcements": Announcement.get_recent(3),
        "events": Event.get_next(3),
        "past_events": Event.get_recent_past(3),
    }

    if session["role"] == "admin":
        data["stats"] = {
            "residents": User.count_residents(),
            "announcements": Announcement.count(),
            "events": Event.count_upcoming(),
            "tickets": Ticket.count_by_status(),
        }
        data["tickets"] = Ticket.get_recent(5)
    else:
        data["stats"] = {"tickets": Ticket.count_by_status(session["user_id"])}
        data["tickets"] = Ticket.get_recent(5, user_id=session["user_id"])

    return render_template(
        "dashboard.html", name=session["name"], role=session["role"],
        show_welcome_modal=show_welcome_modal, **data
    )
