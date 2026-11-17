from flask import Blueprint, render_template, redirect, url_for, flash, request

from forms import ResendVerificationForm, VerificationCodeForm
from mailer import Mailer
from models.user import User

verification_bp = Blueprint("verification", __name__)


@verification_bp.route("/verify/<token>")
def old_verification_link(token):
    flash("Email verification now uses a 6-digit code. Request a new code to continue.", "info")
    return redirect(url_for("verification.resend"))


@verification_bp.route("/verify-email", methods=["GET", "POST"])
def verify_code():
    form = VerificationCodeForm()
    if request.method == "GET":
        form.email.data = request.args.get("email", "").strip().lower()

    if form.validate_on_submit():
        user = User.find_by_email(form.email.data.strip().lower())
        result = user.verify_email_code(form.code.data.strip()) if user else "invalid"

        if result == "verified":
            flash("Email verified. You can now log in.", "success")
            return redirect(url_for("auth.login"))
        if result == "expired":
            flash("That code has expired. Request a new code and try again.", "warning")
        elif result == "locked":
            flash("Too many incorrect attempts. Request a new code before trying again.", "danger")
        else:
            flash("That email and code did not match. Check the 6-digit code and try again.", "danger")

    return render_template("verify_email.html", form=form)


@verification_bp.route("/resend-verification", methods=["GET", "POST"])
def resend():
    form = ResendVerificationForm()
    if request.method == "GET":
        form.email.data = request.args.get("email", "").strip().lower()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.find_by_email(email)
        if user and not user.is_verified:
            code = user.issue_verification_code()
            if code:
                if Mailer.send_verification(user, code):
                    flash("A new verification code was sent. It expires in 10 minutes.", "success")
                else:
                    flash("We could not send the code email. Check the app's email settings and try again.", "warning")
            else:
                flash("Please wait one minute between code requests, or log in if the account is already verified.", "info")
        else:
            flash("If that email has an account waiting for verification, you can request a new code.", "info")
        return redirect(url_for("verification.verify_code", email=email))
    return render_template("resend_verification.html", form=form)
