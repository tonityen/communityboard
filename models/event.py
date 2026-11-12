from models.database import Database
from models.post import Post

BASE_SELECT = """
    SELECT e.*, COALESCE(u.full_name, 'Former admin') AS author_name
    FROM events e
    LEFT JOIN users u ON e.created_by = u.id
"""


class Event(Post):
    """A community event posted by a barangay admin."""

    table = "events"

    def __init__(self, id, title, description, event_date, location,
                 created_by, created_at=None, author_name=None):
        super().__init__(id, title, created_by, created_at, author_name)
        self.description = description
        self.event_date = event_date
        self.location = location

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            row["id"], row["title"], row["description"], row["event_date"],
            row["location"], row["created_by"], row["created_at"], row.get("author_name"),
        )

    @classmethod
    def get_upcoming(cls):
        rows = Database.query(BASE_SELECT + " WHERE e.event_date >= CURDATE() ORDER BY e.event_date ASC")
        return [cls.from_row(row) for row in rows]

    @classmethod
    def get_past(cls):
        rows = Database.query(BASE_SELECT + " WHERE e.event_date < CURDATE() ORDER BY e.event_date DESC")
        return [cls.from_row(row) for row in rows]

    @classmethod
    def get_next(cls, limit=3):
        rows = Database.query(
            BASE_SELECT + " WHERE e.event_date >= CURDATE() ORDER BY e.event_date ASC LIMIT %s", (limit,)
        )
        return [cls.from_row(row) for row in rows]

    @classmethod
    def count_upcoming(cls):
        row = Database.query("SELECT COUNT(*) AS total FROM events WHERE event_date >= CURDATE()", one=True)
        return row["total"]

    @classmethod
    def get_by_id(cls, event_id):
        row = Database.query(BASE_SELECT + " WHERE e.id = %s", (event_id,), one=True)
        return cls.from_row(row)

    @classmethod
    def create(cls, title, description, event_date, location, created_by):
        return Database.execute(
            "INSERT INTO events (title, description, event_date, location, created_by) "
            "VALUES (%s, %s, %s, %s, %s)",
            (title, description, event_date, location, created_by),
        )

    def update(self, title, description, event_date, location):
        Database.execute(
            "UPDATE events SET title = %s, description = %s, event_date = %s, location = %s WHERE id = %s",
            (title, description, event_date, location, self.id),
        )
        self.title = title
        self.description = description
        self.event_date = event_date
        self.location = location