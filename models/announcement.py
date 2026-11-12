from models.database import Database
from models.post import Post

BASE_SELECT = """
    SELECT a.*, COALESCE(u.full_name, 'Former admin') AS author_name
    FROM announcements a
    LEFT JOIN users u ON a.created_by = u.id
"""


class Announcement(Post):
    table = "announcements"

    def __init__(self, id, title, content, created_by, created_at=None, author_name=None):
        super().__init__(id, title, created_by, created_at, author_name)
        self.content = content

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            row["id"], row["title"], row["content"], row["created_by"],
            row["created_at"], row.get("author_name"),
        )

    @classmethod
    def get_all(cls):
        rows = Database.query(BASE_SELECT + " ORDER BY a.created_at DESC")
        return [cls.from_row(row) for row in rows]

    @classmethod
    def get_recent(cls, limit=3):
        rows = Database.query(BASE_SELECT + " ORDER BY a.created_at DESC LIMIT %s", (limit,))
        return [cls.from_row(row) for row in rows]

    @classmethod
    def count(cls):
        return Database.query("SELECT COUNT(*) AS total FROM announcements", one=True)["total"]

    @classmethod
    def latest(cls, limit=3):
        rows = Database.query(
            BASE_SELECT + " ORDER BY a.created_at DESC LIMIT %s", (int(limit),)
        )
        return [cls.from_row(row) for row in rows]

    @classmethod
    def count(cls):
        row = Database.query("SELECT COUNT(*) AS total FROM announcements", one=True)
        return row["total"]

    @classmethod
    def get_by_id(cls, announcement_id):
        row = Database.query(BASE_SELECT + " WHERE a.id = %s", (announcement_id,), one=True)
        return cls.from_row(row)

    @classmethod
    def create(cls, title, content, created_by):
        return Database.execute(
            "INSERT INTO announcements (title, content, created_by) VALUES (%s, %s, %s)",
            (title, content, created_by),
        )

    def update(self, title, content):
        Database.execute(
            "UPDATE announcements SET title = %s, content = %s WHERE id = %s",
            (title, content, self.id),
        )
        self.title = title
        self.content = content