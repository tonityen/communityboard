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
        cls.ensure_verification_code_columns()
        cls.ensure_content_image_columns()
        cls.ensure_ticket_endorsements_table()
        cls.ensure_ticket_followup_columns()
        cls.ensure_content_category_columns()

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
    def ensure_verification_code_columns(cls):
        rows = cls.query("SHOW COLUMNS FROM users")
        names = {row["Field"] for row in rows}
        columns = {
            "verification_code_hash": "CHAR(64) NULL",
            "verification_code_expires_at": "DATETIME NULL",
            "verification_code_sent_at": "DATETIME NULL",
            "verification_attempts": "TINYINT UNSIGNED NOT NULL DEFAULT 0",
        }
        for name, definition in columns.items():
            if name not in names:
                cls.execute(f"ALTER TABLE users ADD COLUMN {name} {definition}")

    @classmethod
    def ensure_ticket_endorsements_table(cls):
        cls.execute(
            "CREATE TABLE IF NOT EXISTS ticket_endorsements ("
            "id INT AUTO_INCREMENT PRIMARY KEY, "
            "ticket_id INT NOT NULL, user_id INT NOT NULL, "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
            "UNIQUE KEY unique_ticket_endorsement (ticket_id, user_id), "
            "FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE, "
            "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
        )

    @classmethod
    def ensure_ticket_followup_columns(cls):
        rows = cls.query("SHOW COLUMNS FROM tickets")
        names = {row["Field"] for row in rows}
        columns = {
            "incident_location": "VARCHAR(150) NULL",
            "incident_date": "DATE NULL",
            "resolution_note": "TEXT NULL",
            "updated_at": "DATETIME NULL",
        }
        for name, definition in columns.items():
            if name not in names:
                cls.execute(f"ALTER TABLE tickets ADD COLUMN {name} {definition}")

    @classmethod
    def ensure_content_category_columns(cls):
        for table in ("announcements", "events"):
            rows = cls.query(f"SHOW COLUMNS FROM {table}")
            if "category" not in {row["Field"] for row in rows}:
                cls.execute(f"ALTER TABLE {table} ADD COLUMN category VARCHAR(40) NOT NULL DEFAULT 'General'")

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
