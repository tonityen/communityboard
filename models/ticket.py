from models.database import Database

BASE_SELECT = """
    SELECT t.*, u.full_name AS reporter_name, u.email AS reporter_email
    FROM tickets t
    JOIN users u ON t.user_id = u.id
"""


class Ticket:
    """A concern a resident reports to the municipality."""

    CATEGORIES = [
        "Road and infrastructure",
        "Garbage and sanitation",
        "Peace and order",
        "Water and electricity",
        "Health",
        "Other",
    ]
    STATUSES = ["open", "in_progress", "resolved"]

    def __init__(self, id, user_id, category, subject, description,
                 status="open", created_at=None, reporter_name=None, reporter_email=None):
        self.id = id
        self.user_id = user_id
        self.category = category
        self.subject = subject
        self.description = description
        self.status = status
        self.created_at = created_at
        self.reporter_name = reporter_name
        self.reporter_email = reporter_email

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            row["id"], row["user_id"], row["category"], row["subject"],
            row["description"], row["status"], row["created_at"],
            row.get("reporter_name"), row.get("reporter_email"),
        )

    @classmethod
    def get_all(cls):
        rows = Database.query(BASE_SELECT + " ORDER BY t.created_at DESC")
        return [cls.from_row(row) for row in rows]

    @classmethod
    def get_by_user(cls, user_id):
        rows = Database.query(
            BASE_SELECT + " WHERE t.user_id = %s ORDER BY t.created_at DESC", (user_id,)
        )
        return [cls.from_row(row) for row in rows]

    @classmethod
    def get_recent(cls, limit=5, user_id=None):
        """The newest tickets. Pass a user_id to see only that resident's tickets."""
        if user_id is None:
            rows = Database.query(BASE_SELECT + " ORDER BY t.created_at DESC LIMIT %s", (limit,))
        else:
            rows = Database.query(
                BASE_SELECT + " WHERE t.user_id = %s ORDER BY t.created_at DESC LIMIT %s",
                (user_id, limit),
            )
        return [cls.from_row(row) for row in rows]

    @classmethod
    def count_by_status(cls, user_id=None):
        """Returns {'open': n, 'in_progress': n, 'resolved': n}. Optional: one resident only."""
        sql = "SELECT status, COUNT(*) AS total FROM tickets"
        params = ()
        if user_id is not None:
            sql += " WHERE user_id = %s"
            params = (user_id,)
        sql += " GROUP BY status"
        counts = {status: 0 for status in cls.STATUSES}
        for row in Database.query(sql, params):
            counts[row["status"]] = row["total"]
        return counts

    @classmethod
    def get_by_id(cls, ticket_id):
        row = Database.query(BASE_SELECT + " WHERE t.id = %s", (ticket_id,), one=True)
        return cls.from_row(row)

    @classmethod
    def create(cls, user_id, category, subject, description):
        new_id = Database.execute(
            "INSERT INTO tickets (user_id, category, subject, description) VALUES (%s, %s, %s, %s)",
            (user_id, category, subject, description),
        )
        return cls.get_by_id(new_id)

    def update_details(self, category, subject, description):
        Database.execute(
            "UPDATE tickets SET category = %s, subject = %s, description = %s WHERE id = %s",
            (category, subject, description, self.id),
        )
        self.category = category
        self.subject = subject
        self.description = description

    def update_status(self, new_status):
        if new_status not in self.STATUSES:
            raise ValueError("Invalid status")
        Database.execute("UPDATE tickets SET status = %s WHERE id = %s", (new_status, self.id))
        self.status = new_status

    def delete(self):
        Database.execute("DELETE FROM tickets WHERE id = %s", (self.id,))
