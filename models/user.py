import hashlib

from werkzeug.security import generate_password_hash, check_password_hash

from models.database import Database


class User:

    MAX_FAILED_LOGINS = 5
    LOCK_MINUTES = 15

    def __init__(self, id, full_name, email, password_hash, role="resident",
                 created_at=None, is_verified=False, photo=None,
                 username=None, contact_number=None, purok=None,
                 status="active", failed_attempts=0, locked_until=None):
        self.id = id
        self.full_name = full_name
        self.email = email
        self.__password_hash = password_hash  
        self.role = role
        self.created_at = created_at
        self.is_verified = bool(is_verified)
        self.photo = photo
        self.username = username
        self.contact_number = contact_number
        self.purok = purok
        self.status = status or "active"
        self.failed_attempts = failed_attempts or 0
        self.locked_until = locked_until

    def check_password(self, password):
        return check_password_hash(self.__password_hash, password)

    def is_admin(self):
        return self.role == "admin"

    def is_disabled(self):
        return self.status == "disabled"

    def refresh_lock_state(self):
        Database.execute(
            "UPDATE users SET failed_attempts = 0, locked_until = NULL "
            "WHERE id = %s AND locked_until IS NOT NULL AND locked_until <= NOW()",
            (self.id,),
        )
        row = Database.query(
            "SELECT failed_attempts, locked_until, "
            "(locked_until IS NOT NULL AND locked_until > NOW()) AS is_locked "
            "FROM users WHERE id = %s",
            (self.id,),
            one=True,
        )
        self.failed_attempts = row["failed_attempts"]
        self.locked_until = row["locked_until"]
        return bool(row["is_locked"])

    def register_failed_login(self):
        """Count one wrong password. Returns True when this attempt locks the account."""
        attempts = self.failed_attempts + 1
        if attempts >= self.MAX_FAILED_LOGINS:
            Database.execute(
                "UPDATE users SET failed_attempts = %s, "
                "locked_until = DATE_ADD(NOW(), INTERVAL %s MINUTE) WHERE id = %s",
                (attempts, self.LOCK_MINUTES, self.id),
            )
            self.failed_attempts = attempts
            return True
        Database.execute(
            "UPDATE users SET failed_attempts = %s WHERE id = %s",
            (attempts, self.id),
        )
        self.failed_attempts = attempts
        return False

    def clear_failed_logins(self):
        Database.execute(
            "UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = %s",
            (self.id,),
        )
        self.failed_attempts = 0
        self.locked_until = None

    def mark_verified(self):
        Database.execute("UPDATE users SET is_verified = 1 WHERE id = %s", (self.id,))
        self.is_verified = True

    def password_fingerprint(self):
        return hashlib.sha256(self.__password_hash.encode()).hexdigest()[:16]

    def update_password(self, new_password):
        hashed = generate_password_hash(new_password)
        Database.execute("UPDATE users SET password_hash = %s WHERE id = %s", (hashed, self.id))
        self.__password_hash = hashed

    def update_profile(self, full_name, email):
        if email != self.email:
            Database.execute(
                "UPDATE users SET full_name = %s, email = %s, is_verified = 0 WHERE id = %s",
                (full_name, email, self.id),
            )
            self.is_verified = False
        else:
            Database.execute("UPDATE users SET full_name = %s WHERE id = %s", (full_name, self.id))
        self.full_name = full_name
        self.email = email

    def set_photo(self, filename):
        Database.execute("UPDATE users SET photo = %s WHERE id = %s", (filename, self.id))
        self.photo = filename

    def delete_account(self):
        """Delete this account. Their tickets are deleted; announcements and events stay."""
        Database.run_all([
            ("DELETE FROM tickets WHERE user_id = %s", (self.id,)),
            ("UPDATE announcements SET created_by = NULL WHERE created_by = %s", (self.id,)),
            ("UPDATE events SET created_by = NULL WHERE created_by = %s", (self.id,)),
            ("DELETE FROM users WHERE id = %s", (self.id,)),
        ])

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            row["id"], row["full_name"], row["email"], row["password_hash"],
            row["role"], row["created_at"], row["is_verified"], row["photo"],
            username=row["username"], contact_number=row["contact_number"], purok=row["purok"],
            status=row.get("status", "active"),
            failed_attempts=row.get("failed_attempts", 0),
            locked_until=row.get("locked_until"),
        )

    @classmethod
    def find_by_email(cls, email):
        row = Database.query("SELECT * FROM users WHERE email = %s", (email,), one=True)
        return cls.from_row(row)

    @classmethod
    def find_by_username(cls, username):
        row = Database.query("SELECT * FROM users WHERE username = %s", (username,), one=True)
        return cls.from_row(row)

    @classmethod
    def find_by_login(cls, identifier):
        """Look up a person by email when the text contains @, otherwise by username."""
        identifier = (identifier or "").strip().lower()
        if "@" in identifier:
            return cls.find_by_email(identifier)
        return cls.find_by_username(identifier)

    @classmethod
    def find_by_id(cls, user_id):
        row = Database.query("SELECT * FROM users WHERE id = %s", (user_id,), one=True)
        return cls.from_row(row)

    @classmethod
    def count_admins(cls):
        row = Database.query("SELECT COUNT(*) AS total FROM users WHERE role = 'admin'", one=True)
        return row["total"]
    
    @classmethod
    def count_residents(cls):
        row = Database.query("SELECT COUNT(*) AS total FROM users WHERE role = 'resident'", one=True)
        return row["total"]

    @classmethod
    def create(cls, full_name, email, password, role="resident",
               username=None, contact_number=None, purok=None):
        hashed = generate_password_hash(password)
        new_id = Database.execute(
            "INSERT INTO users (full_name, email, password_hash, role, username, contact_number, purok) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (full_name, email, hashed, role, username, contact_number, purok),
        )
        return cls.find_by_id(new_id)