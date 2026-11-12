from flask import Blueprint, render_template, redirect, url_for, flash, session, abort

from forms import EventForm
from models.event import Event
from routes.announcements import admin_required
from routes.auth import login_required

events_bp = Blueprint("events", __name__, url_prefix="/events")


@events_bp.route("/")
@login_required
def list_events():
    return render_template(
        "events/list.html", upcoming=Event.get_upcoming(), past=Event.get_past()
    )


@events_bp.route("/new", methods=["GET", "POST"])
@login_required
@admin_required
def create_event():
    form = EventForm()
    if form.validate_on_submit():
        Event.create(
            form.title.data.strip(),
            form.description.data.strip(),
            form.event_date.data,
            (form.location.data or "").strip() or None,
            session["user_id"],
        )
        flash("Event posted.", "success")
        return redirect(url_for("events.list_events"))
    return render_template("events/form.html", form=form, event=None)


@events_bp.route("/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_event(event_id):
    event = Event.get_by_id(event_id)
    if event is None:
        abort(404)
    form = EventForm(obj=event)
    if form.validate_on_submit():
        event.update(
            form.title.data.strip(),
            form.description.data.strip(),
            form.event_date.data,
            (form.location.data or "").strip() or None,
        )
        flash("Event updated.", "success")
        return redirect(url_for("events.list_events"))
    return render_template("events/form.html", form=form, event=event)


@events_bp.route("/<int:event_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_event(event_id):
    event = Event.get_by_id(event_id)
    if event is None:
        abort(404)
    event.delete()
    flash("Event deleted.", "info")
    return redirect(url_for("events.list_events"))