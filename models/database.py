import mysql.connector


class Database:

    _config = {}

    @classmethod
    def init_app(cls, app):
        cls._config = {
            "host": app.config["DB_HOST"],
            "user": app.config["DB_USER"],
            "password": app.config["DB_PASSWORD"],
            "database": app.config["DB_NAME"],
        }
        cls.ensure_login_columns()
        cls.ensure_content_image_columns()

    @classmethod
    def ensure_login_columns(cls):
        rows = cls.query("SHOW COLUMNS FROM users")
        names = {row["Field"] for row in rows}
        statements = []
        if "status" not in names:
            statements.append(
                "ADD COLUMN status ENUM('active', 'disabled') NOT NULL DEFAULT 'active'"
            )
        if "failed_attempts" not in names:
            statements.append("ADD COLUMN failed_attempts INT NOT NULL DEFAULT 0")
        if "locked_until" not in names:
            statements.append("ADD COLUMN locked_until DATETIME NULL")
        if statements:
            cls.execute("ALTER TABLE users " + ", ".join(statements))

    @classmethod
    def ensure_content_image_columns(cls):
        """Add optional image fields to databases created before content photos were supported."""
        for table in ("announcements", "events"):
            rows = cls.query(f"SHOW COLUMNS FROM {table}")
            names = {row["Field"] for row in rows}
            if "image" not in names:
                cls.execute(f"ALTER TABLE {table} ADD COLUMN image VARCHAR(255) NULL")

    @classmethod
    def query(cls, sql, params=(), one=False):
        conn = mysql.connector.connect(**cls._config)
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            if one:
                return rows[0] if rows else None
            return rows
        finally:
            conn.close()

    @classmethod
    def execute(cls, sql, params=()):
        conn = mysql.connector.connect(**cls._config)
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    @classmethod
    def run_all(cls, statements):
        conn = mysql.connector.connect(**cls._config)
        try:
            cursor = conn.cursor()
            for sql, params in statements:
               cursor.execute(sql, params)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
