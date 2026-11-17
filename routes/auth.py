import hmac
from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, session, current_app

from forms import RegisterForm, LoginForm, AdminRegisterForm
from mailer import Mailer
from models.user import User

auth_bp = Blueprint("auth", __name__)


def login_required(view):
    """Send guests, and people whose account is disabled, back to the login page."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            flash("Please log in first.", "warning")
            return redirect(url_for("auth.login"))
        user = User.find_by_id(user_id)
        if user is None:
            session.clear()
            flash("Please log in first.", "warning")
            return redirect(url_for("auth.login"))
        if user.is_disabled():
            session.clear()
            flash("This account is disabled. Contact the barangay office.", "danger")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


def start_session(user, remember):
    """Store who is logged in. Remember-me keeps that login for 14 days."""
    session.clear()
    session.permanent = bool(remember)
    session["user_id"] = user.id
    session["name"] = user.full_name
    session["role"] = user.role


def create_account(form, role):
    """Create the account and email its verification code."""
    email = form.email.data.strip().lower()
    if User.find_by_email(email):
        flash("That email is already registered.", "danger")
        return False

    user = User.create(
        form.full_name.data, email, form.password.data, role,
        username=form.username.data, contact_number=form.contact_number.data, purok=form.purok.data,
    )
    code = user.issue_verification_code()
    if code and Mailer.send_verification(user, code):
        flash("Account created. Enter the 6-digit code we emailed you to verify your account.", "success")
    else:
        flash("Account created, but the code email could not be sent. You can request a new code from the login page.", "warning")
    return True


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit() and create_account(form, "resident"):
        return redirect(url_for("verification.verify_code", email=form.email.data.strip().lower()))
    return render_template("register.html", form=form)


@auth_bp.route("/admin/register", methods=["GET", "POST"])
def admin_register():
    form = AdminRegisterForm()
    if form.validate_on_submit():
        secret_code = current_app.config["ADMIN_ACCESS_CODE"]
        typed_code = form.access_code.data
        if not secret_code or not hmac.compare_digest(typed_code.encode(), secret_code.encode()):
            flash("Invalid admin access code.", "danger")
        elif create_account(form, "admin"):
            return redirect(url_for("verification.verify_code", email=form.email.data.strip().lower()))
    return render_template("admin_register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.find_by_login(form.identifier.data)
        if user is None:
            flash("Wrong username/email or password.", "danger")
        elif user.refresh_lock_state():
            flash("Too many failed logins. This account is locked for 15 minutes.", "danger")
        elif not user.check_password(form.password.data):
            locked = user.register_failed_login()
            if locked:
                flash("Too many failed logins. This account is locked for 15 minutes.", "danger")
            else:
                left = user.MAX_FAILED_LOGINS - user.failed_attempts
                flash(f"Wrong username/email or password. {left} attempt(s) left.", "danger")
        elif user.is_disabled():
            flash("This account is disabled. Contact the barangay office.", "danger")
        elif not user.is_verified:
            flash("Please verify your email with the 6-digit code in your inbox.", "warning")
        else:
            user.clear_failed_logins()
            start_session(user, form.remember.data)
            session["show_welcome_modal"] = True
            return redirect(url_for("main.dashboard"))
    return render_template("login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))
