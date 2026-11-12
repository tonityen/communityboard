import os
import secrets
from functools import wraps

from flask import (
    Blueprint, render_template, redirect, url_for, flash, session, current_app,
)

from forms import ProfileForm, ChangePasswordForm, PhotoForm, DeleteAccountForm
from mailer import Mailer
from models.user import User
from routes.auth import login_required

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")

MAX_PHOTO_BYTES = 2 * 1024 * 1024  # 2 MB


def with_current_user(view):
    """Give the page the logged-in user (and log out if that account no longer exists)."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = User.find_by_id(session["user_id"])
        if user is None:
            session.clear()
            return redirect(url_for("auth.login"))
        return view(user, *args, **kwargs)
    return wrapped


def photo_folder():
    folder = os.path.join(current_app.static_folder, "uploads", "profiles")
    os.makedirs(folder, exist_ok=True)
    return folder


def delete_photo_file(filename):
    if filename:
        path = os.path.join(photo_folder(), os.path.basename(filename))
        if os.path.exists(path):
            os.remove(path)


def image_extension(data):
    """Look at the first bytes of the file to be sure it is really a JPG or PNG."""
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    return None


def show_page(user, details_form=None, password_form=None, photo_form=None, delete_form=None):
    """Show the profile page. Forms that were not just submitted start fresh."""
    return render_template(
        "profile.html",
        user=user,
        details_form=details_form or ProfileForm(formdata=None, obj=user),
        password_form=password_form or ChangePasswordForm(formdata=None),
        photo_form=photo_form or PhotoForm(formdata=None),
        delete_form=delete_form or DeleteAccountForm(formdata=None),
    )


@profile_bp.route("/")
@login_required
@with_current_user
def view_profile(user):
    return show_page(user)


@profile_bp.route("/details", methods=["POST"])
@login_required
@with_current_user
def update_details(user):
    form = ProfileForm()
    if form.validate_on_submit():
        new_name = form.full_name.data.strip()
        new_email = form.email.data.strip().lower()

        if new_email != user.email:
            if User.find_by_email(new_email):
                flash("That email is already used by another account.", "danger")
                return show_page(user, details_form=form)
            user.update_profile(new_name, new_email)
            Mailer.send_verification(user)
            session.clear()
            flash("Your email was changed. We sent a verification link to the new address. Please verify it, then log in.", "info")
            return redirect(url_for("auth.login"))

        user.update_profile(new_name, user.email)
        session["name"] = new_name
        flash("Profile updated.", "success")
        return redirect(url_for("profile.view_profile"))
    return show_page(user, details_form=form)


@profile_bp.route("/password", methods=["POST"])
@login_required
@with_current_user
def change_password(user):
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not user.check_password(form.current_password.data):
            flash("Your current password is wrong.", "danger")
            return show_page(user, password_form=form)
        user.update_password(form.password.data)
        flash("Password changed.", "success")
        return redirect(url_for("profile.view_profile"))
    return show_page(user, password_form=form)


@profile_bp.route("/photo", methods=["POST"])
@login_required
@with_current_user
def update_photo(user):
    form = PhotoForm()
    if form.validate_on_submit():
        data = form.photo.data.read()
        if len(data) > MAX_PHOTO_BYTES:
            flash("That photo is too big. Please choose one under 2 MB.", "danger")
            return show_page(user, photo_form=form)

        extension = image_extension(data)
        if extension is None:
            flash("That file is not a real JPG or PNG image.", "danger")
            return show_page(user, photo_form=form)

        filename = f"user_{user.id}_{secrets.token_hex(8)}.{extension}"
        with open(os.path.join(photo_folder(), filename), "wb") as saved_file:
            saved_file.write(data)
        delete_photo_file(user.photo)
        user.set_photo(filename)
        flash("Profile photo updated.", "success")
        return redirect(url_for("profile.view_profile"))
    return show_page(user, photo_form=form)


@profile_bp.route("/delete", methods=["POST"])
@login_required
@with_current_user
def delete_account(user):
    form = DeleteAccountForm()
    if form.validate_on_submit():
        if not user.check_password(form.account_password.data):
            flash("Wrong password. Your account was not deleted.", "danger")
            return show_page(user, delete_form=form)

        if user.is_admin() and User.count_admins() <= 1:
            flash("You are the only admin, so this account cannot be deleted. Make another admin first.", "danger")
            return show_page(user, delete_form=form)

        old_photo = user.photo
        user.delete_account()
        delete_photo_file(old_photo)
        session.clear()
        flash("Your account was deleted.", "info")
        return redirect(url_for("main.index"))
    return show_page(user, delete_form=form)