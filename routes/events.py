from flask import Blueprint, render_template, redirect, url_for, flash, session, abort, request

from forms import EventForm
from content_images import delete_content_image, save_content_image
from models.event import Event
from routes.announcements import admin_required
from routes.auth import login_required

events_bp = Blueprint("events", __name__, url_prefix="/events")


@events_bp.route("/")
@login_required
def list_events():
    query = (request.args.get("q") or "").strip()
    period = request.args.get("period", "upcoming")
    category = (request.args.get("category") or "").strip()
    upcoming, past = Event.get_upcoming(), Event.get_past()
    if query:
        needle = query.casefold()
        match = lambda e: needle in e.title.casefold() or needle in e.description.casefold() or needle in (e.location or "").casefold()
        upcoming = [e for e in upcoming if match(e)]
        past = [e for e in past if match(e)]
    if category:
        upcoming = [e for e in upcoming if e.category == category]
        past = [e for e in past if e.category == category]
    if period == "upcoming":
        past = []
    elif period == "past":
        upcoming = []
    return render_template(
        "events/list.html", upcoming=upcoming, past=past, query=query, period=period,
        categories=sorted({e.category for e in Event.get_upcoming() + Event.get_past()}), category=category
    )


@events_bp.route("/new", methods=["GET", "POST"])
@login_required
@admin_required
def create_event():
    form = EventForm()
    if form.validate_on_submit():
        try:
            image = save_content_image(form.photo.data, "events")
        except ValueError as error:
            flash(str(error), "danger")
            return render_template("events/form.html", form=form, event=None)
        Event.create(
            form.title.data.strip(),
            form.description.data.strip(),
            form.event_date.data,
            (form.location.data or "").strip() or None,
            session["user_id"],
            image,
            form.category.data,
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
        try:
            new_image = save_content_image(form.photo.data, "events")
        except ValueError as error:
            flash(str(error), "danger")
            return render_template("events/form.html", form=form, event=event)
        old_image = event.image
        event.update(
            form.title.data.strip(),
            form.description.data.strip(),
            form.event_date.data,
            (form.location.data or "").strip() or None,
            new_image or old_image,
            form.category.data,
        )
        if new_image:
            delete_content_image("events", old_image)
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
    image = event.image
    event.delete()
    delete_content_image("events", image)
    flash("Event deleted.", "info")
    return redirect(url_for("events.list_events"))
