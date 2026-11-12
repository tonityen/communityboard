from models.database import Database


class Post:
    """Base class for anything an admin publishes (announcements, events)."""

    table = None  # each child class sets its own table name

    def __init__(self, id, title, created_by, created_at=None, author_name=None):
        self.id = id
        self.title = title
        self.created_by = created_by
        self.created_at = created_at
        self.author_name = author_name

    def delete(self):
        Database.execute(f"DELETE FROM {self.table} WHERE id = %s", (self.id,))