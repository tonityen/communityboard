from flask import Blueprint, render_template, redirect, url_for, flash

from forms import ForgotPasswordForm, ResetPasswordForm
from mailer import Mailer
from models.user import User
from tokens import TokenService

password_reset_bp = Blueprint("password_reset", __name__)

RESET_MAX_AGE = 30 * 60  # the reset link works for 30 minutes


@password_reset_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.find_by_email(form.email.data.strip().lower())
        if user and user.is_verified:
            Mailer.send_password_reset(user)
        # Same message whether or not the email exists, so nobody can check who has an account.
        flash("If that email has an account, we sent a password reset link. It works for 30 minutes.", "info")
        return redirect(url_for("auth.login"))
    return render_template("forgot_password.html", form=form)


@password_reset_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    data = TokenService.read(token, "reset-password", RESET_MAX_AGE)
    user = User.find_by_id(data["id"]) if data else None

    # The link only works once: after the password changes, the fingerprint no longer matches.
    if user is None or user.password_fingerprint() != data["fp"]:
        flash("That reset link is invalid or has expired. Please request a new one.", "danger")
        return redirect(url_for("password_reset.forgot_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.update_password(form.password.data)
        flash("Your password was changed. You can log in now.", "success")
        return redirect(url_for("auth.login"))
    return render_template("reset_password.html", form=form)