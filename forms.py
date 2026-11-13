import re

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import (
    StringField, PasswordField, EmailField, TextAreaField, SelectField, DateField, BooleanField,
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, Optional, Regexp, ValidationError,
)

from models.user import User
from puroks import PUROKS


# ---------- small helpers used by several forms ----------

def strip_text(value):
    return value.strip() if isinstance(value, str) else value


def lower_text(value):
    return value.lower() if isinstance(value, str) else value


def strong_password(form, field):
    """The password needs an uppercase letter, a lowercase letter, a number and a special character."""
    password = field.data or ""
    has_upper = re.search(r"[A-Z]", password)
    has_lower = re.search(r"[a-z]", password)
    has_number = re.search(r"[0-9]", password)
    has_special = re.search(r"[^A-Za-z0-9]", password)
    if not (has_upper and has_lower and has_number and has_special):
        raise ValidationError("Password must include uppercase, lowercase, number, and special character.")

def no_repeated_digits(form, field):
    """Reject a number that has the same digit 4 or more times in a row, like 09123444412."""
    if re.search(r"([0-9])\1{3}", field.data or ""):
        raise ValidationError("Contact number cannot have the same digit repeated 4 or more times in a row.")


# ---------- registration and login ----------

class RegisterForm(FlaskForm):
    full_name = StringField("Full name", validators=[
        DataRequired(message="Full name is required."),
        Regexp(r"^[^\W\d_]+(?:[ '\-]+[^\W\d_]+)*$",
               message="Full name can only contain letters, spaces, hyphens, and apostrophes."),
        Length(min=2, message="Full name must contain at least 2 characters."),
        Length(max=100, message="Full name must not be longer than 100 characters."),
    ], filters=[strip_text])

    username = StringField("Username", validators=[
        DataRequired(message="Username is required."),
        Regexp(r"^[A-Za-z0-9_]+$", message="Username can only contain letters, numbers, and underscores."),
        Length(min=4, max=20, message="Username must be 4 to 20 characters long."),
    ], filters=[strip_text, lower_text])

    email = EmailField("Email address", validators=[
        DataRequired(message="Email address is required."),
        Email(message="Please enter a valid email address."),
        Length(max=120, message="Email address must not be longer than 120 characters."),
    ], filters=[strip_text, lower_text])

    contact_number = StringField("Contact number", validators=[
        DataRequired(message="Contact number is required."),
        Regexp(r"^09[0-9]{9}$", message="Please enter a valid 11-digit Philippine mobile number."),
        no_repeated_digits,
    ], filters=[strip_text])

    purok = SelectField(
        "Purok / Area",
        choices=[("", "Select your purok / area")] + [(name, name) for name in PUROKS],
        validators=[DataRequired(message="Please select your purok / area.")],
    )

    password = PasswordField("Password", validators=[
        DataRequired(message="Password is required."),
        Length(min=8, message="Password must contain at least 8 characters."),
        Length(max=64, message="Password must not be longer than 64 characters."),
        strong_password,
    ])

    confirm_password = PasswordField("Confirm password", validators=[
        DataRequired(message="Please confirm your password."),
        EqualTo("password", message="Passwords do not match."),
    ])

    def validate_username(self, field):
        if User.find_by_username(field.data):
            raise ValidationError("Username is already taken.")

    def validate_email(self, field):
        if User.find_by_email(field.data):
            raise ValidationError("Email address is already registered.")


def username_or_email(form, field):
    """Accept a username, or an email when the value contains @."""
    value = (field.data or "").strip()
    if "@" in value:
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValidationError("Please enter a valid email address.")
        return
    if not re.fullmatch(r"[A-Za-z0-9_]{4,20}", value):
        raise ValidationError("Username must be 4 to 20 characters: letters, numbers, and underscores.")


class LoginForm(FlaskForm):
    identifier = StringField("Username or email", validators=[
        DataRequired(message="Username or email is required."),
        Length(max=120, message="Username or email must not be longer than 120 characters."),
        username_or_email,
    ], filters=[strip_text, lower_text])
    password = PasswordField("Password", validators=[
        DataRequired(message="Password is required."),
    ])
    remember = BooleanField("Remember me on this device")


class AdminRegisterForm(RegisterForm):
    access_code = PasswordField("Admin access code", validators=[
        DataRequired(message="Admin access code is required."),
    ])


class ResendVerificationForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])


class ForgotPasswordForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])


class ResetPasswordForm(FlaskForm):
    password = PasswordField("New password", validators=[
        DataRequired(message="Password is required."),
        Length(min=8, message="Password must contain at least 8 characters."),
        Length(max=64, message="Password must not be longer than 64 characters."),
        strong_password,
    ])
    confirm_password = PasswordField(
        "Confirm new password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )


class AnnouncementForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=3, max=150)])
    content = TextAreaField("Content", validators=[DataRequired(), Length(min=10, max=5000)])
    photo = FileField("Optional photo", validators=[FileAllowed(["jpg", "jpeg", "png"], "Choose a JPG or PNG image.")])


class TicketForm(FlaskForm):
    category = SelectField("Category", validators=[DataRequired()])
    subject = StringField("Subject", validators=[DataRequired(), Length(min=5, max=150)])
    description = TextAreaField("Describe the concern", validators=[DataRequired(), Length(min=20, max=2000)])


class EventForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=3, max=150)])
    event_date = DateField("Event date", validators=[DataRequired()])
    location = StringField("Location", validators=[Optional(), Length(max=150)])
    description = TextAreaField("Description", validators=[DataRequired(), Length(min=10, max=3000)])
    photo = FileField("Optional photo", validators=[FileAllowed(["jpg", "jpeg", "png"], "Choose a JPG or PNG image.")])


class ProfileForm(FlaskForm):
    full_name = StringField("Full name", validators=[DataRequired(), Length(min=2, max=100)])
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=120)])


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current password", validators=[DataRequired()])
    password = PasswordField("New password", validators=[
        DataRequired(message="Password is required."),
        Length(min=8, message="Password must contain at least 8 characters."),
        Length(max=64, message="Password must not be longer than 64 characters."),
        strong_password,
    ])
    confirm_password = PasswordField(
        "Confirm new password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )


class PhotoForm(FlaskForm):
    photo = FileField(
        "Profile photo",
        validators=[FileRequired(), FileAllowed(["jpg", "jpeg", "png"], "Only JPG or PNG images are allowed.")],
    )


class DeleteAccountForm(FlaskForm):
    account_password = PasswordField("Confirm with your password", validators=[DataRequired()])
