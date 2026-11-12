from flask import Blueprint, render_template, redirect, url_for, flash

from forms import ResendVerificationForm
from mailer import Mailer
from models.user import User
from tokens import TokenService

verification_bp = Blueprint("verification", __name__)

VERIFY_MAX_AGE = 24 * 60 * 60  # the link works for 24 hours


@verification_bp.route("/verify/<token>")
def verify_email(token):
    data = TokenService.read(token, "verify-email", VERIFY_MAX_AGE)
    user = User.find_by_id(data["id"]) if data else None

    if user is None or user.email != data["email"]:
        flash("That verification link is invalid or has expired. You can request a new one.", "danger")
        return redirect(url_for("verification.resend"))

    if user.is_verified:
        flash("Your email is already verified. You can log in.", "info")
    else:
        user.mark_verified()
        flash("Email verified! You can log in now.", "success")
    return redirect(url_for("auth.login"))


@verification_bp.route("/resend-verification", methods=["GET", "POST"])
def resend():
    form = ResendVerificationForm()
    if form.validate_on_submit():
        user = User.find_by_email(form.email.data.strip().lower())
        if user and not user.is_verified:
            Mailer.send_verification(user)
        flash("If that email has an account waiting for verification, we sent a new link.", "info")
        return redirect(url_for("auth.login"))
    return render_template("resend_verification.html", form=form)