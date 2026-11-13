from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, session, abort

from forms import AnnouncementForm
from content_images import delete_content_image, save_content_image
from models.announcement import Announcement
from routes.auth import login_required

announcements_bp = Blueprint("announcements", __name__, url_prefix="/announcements")


def admin_required(view):
    """Only admins can open this page."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Only barangay admins can do that.", "danger")
            return redirect(url_for("main.dashboard"))
        return view(*args, **kwargs)
    return wrapped


@announcements_bp.route("/")
@login_required
def list_announcements():
    announcements = Announcement.get_all()
    return render_template("announcements/list.html", announcements=announcements)


@announcements_bp.route("/new", methods=["GET", "POST"])
@login_required
@admin_required
def create_announcement():
    form = AnnouncementForm()
    if form.validate_on_submit():
        try:
            image = save_content_image(form.photo.data, "announcements")
        except ValueError as error:
            flash(str(error), "danger")
            return render_template("announcements/form.html", form=form, announcement=None)
        Announcement.create(
            form.title.data.strip(), form.content.data.strip(), session["user_id"], image
        )
        flash("Announcement posted.", "success")
        return redirect(url_for("announcements.list_announcements"))
    return render_template("announcements/form.html", form=form, announcement=None)


@announcements_bp.route("/<int:announcement_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_announcement(announcement_id):
    announcement = Announcement.get_by_id(announcement_id)
    if announcement is None:
        abort(404)
    form = AnnouncementForm(obj=announcement)
    if form.validate_on_submit():
        try:
            new_image = save_content_image(form.photo.data, "announcements")
        except ValueError as error:
            flash(str(error), "danger")
            return render_template("announcements/form.html", form=form, announcement=announcement)
        old_image = announcement.image
        announcement.update(
            form.title.data.strip(), form.content.data.strip(), new_image or old_image
        )
        if new_image:
            delete_content_image("announcements", old_image)
        flash("Announcement updated.", "success")
        return redirect(url_for("announcements.list_announcements"))
    return render_template("announcements/form.html", form=form, announcement=announcement)


@announcements_bp.route("/<int:announcement_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_announcement(announcement_id):
    announcement = Announcement.get_by_id(announcement_id)
    if announcement is None:
        abort(404)
    image = announcement.image
    announcement.delete()
    delete_content_image("announcements", image)
    flash("Announcement deleted.", "info")
    return redirect(url_for("announcements.list_announcements"))
