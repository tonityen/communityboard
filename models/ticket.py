from models.database import Database
from difflib import SequenceMatcher
import re


REPORT_STOP_WORDS = {
    "a", "an", "and", "at", "for", "in", "is", "it", "near", "of", "on",
    "the", "there", "to", "was", "were", "with", "please", "reported", "report",
    "concern", "issue", "happened", "happening", "today",
}


def report_similarity(first, second):
    """Compare wording loosely so likely repeat incidents can be shown for confirmation."""
    first_words = [w for w in re.findall(r"[a-z0-9]+", first.casefold()) if w not in REPORT_STOP_WORDS]
    second_words = [w for w in re.findall(r"[a-z0-9]+", second.casefold()) if w not in REPORT_STOP_WORDS]
    first_text = " ".join(first_words)
    second_text = " ".join(second_words)
    if not first_text or not second_text:
        return 0.0
    phrase_score = SequenceMatcher(None, first_text, second_text, autojunk=False).ratio()
    first_set, second_set = set(first_words), set(second_words)
    common_words = first_set & second_set
    overlap_score = len(common_words) / min(len(first_set), len(second_set)) if len(common_words) >= 2 else 0.0
    return max(phrase_score, overlap_score)

BASE_SELECT = """
    SELECT t.*, u.full_name AS reporter_name, u.email AS reporter_email,
           (1 + (SELECT COUNT(*) FROM ticket_endorsements te WHERE te.ticket_id = t.id)) AS support_count
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
                 status="open", created_at=None, reporter_name=None, reporter_email=None,
                 support_count=1, incident_location=None, incident_date=None,
                 resolution_note=None, updated_at=None):
        self.id = id
        self.user_id = user_id
        self.category = category
        self.subject = subject
        self.description = description
        self.status = status
        self.created_at = created_at
        self.reporter_name = reporter_name
        self.reporter_email = reporter_email
        self.support_count = int(support_count or 1)
        self.incident_location = incident_location
        self.incident_date = incident_date
        self.resolution_note = resolution_note
        self.updated_at = updated_at or created_at

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            row["id"], row["user_id"], row["category"], row["subject"],
            row["description"], row["status"], row["created_at"],
            row.get("reporter_name"), row.get("reporter_email"), row.get("support_count", 1),
            row.get("incident_location"), row.get("incident_date"), row.get("resolution_note"), row.get("updated_at"),
        )

    @classmethod
    def get_all(cls):
        rows = Database.query(BASE_SELECT + " ORDER BY t.created_at DESC")
        return [cls.from_row(row) for row in rows]

    @classmethod
    def get_by_user(cls, user_id):
        rows = Database.query(
            BASE_SELECT + " WHERE t.user_id = %s OR EXISTS ("
            "SELECT 1 FROM ticket_endorsements te WHERE te.ticket_id = t.id AND te.user_id = %s) "
            "ORDER BY t.created_at DESC",
            (user_id, user_id),
        )
        return [cls.from_row(row) for row in rows]

    @classmethod
    def get_recent(cls, limit=5, user_id=None):
        """The newest tickets. Pass a user_id to see only that resident's tickets."""
        if user_id is None:
            rows = Database.query(BASE_SELECT + " ORDER BY t.created_at DESC LIMIT %s", (limit,))
        else:
            rows = Database.query(
                BASE_SELECT + " WHERE t.user_id = %s OR EXISTS ("
                "SELECT 1 FROM ticket_endorsements te WHERE te.ticket_id = t.id AND te.user_id = %s) "
                "ORDER BY t.created_at DESC LIMIT %s",
                (user_id, user_id, limit),
            )
        return [cls.from_row(row) for row in rows]

    @classmethod
    def count_by_status(cls, user_id=None):
        """Returns {'open': n, 'in_progress': n, 'resolved': n}. Optional: one resident only."""
        sql = "SELECT t.status, COUNT(DISTINCT t.id) AS total FROM tickets t"
        params = ()
        if user_id is not None:
            sql += " LEFT JOIN ticket_endorsements te ON te.ticket_id = t.id AND te.user_id = %s "
            sql += "WHERE t.user_id = %s OR te.user_id IS NOT NULL "
            params = (user_id, user_id)
        sql += " GROUP BY t.status"
        counts = {status: 0 for status in cls.STATUSES}
        for row in Database.query(sql, params):
            counts[row["status"]] = row["total"]
        return counts

    @classmethod
    def get_by_id(cls, ticket_id):
        row = Database.query(BASE_SELECT + " WHERE t.id = %s", (ticket_id,), one=True)
        return cls.from_row(row)

    @classmethod
    def find_similar_open(cls, category, subject, description, incident_location=None, incident_date=None, limit=40):
        """Return recent active reports in the same category with similar wording."""
        rows = Database.query(
            BASE_SELECT + " WHERE t.category = %s AND t.status IN ('open', 'in_progress') "
            "AND t.created_at >= DATE_SUB(NOW(), INTERVAL 72 HOUR) "
            "ORDER BY t.created_at DESC LIMIT %s",
            (category, limit),
        )
        submitted_text = f"{subject} {description}"
        matches = []
        for row in rows:
            ticket = cls.from_row(row)
            score = report_similarity(submitted_text, f"{ticket.subject} {ticket.description}")
            if incident_location and ticket.incident_location:
                location_score = report_similarity(incident_location, ticket.incident_location)
                score = min(1.0, score + .18) if location_score >= .5 else score * .55 if location_score < .2 else score
            if incident_date and ticket.incident_date:
                days = abs((incident_date - ticket.incident_date).days)
                score = min(1.0, score + .12) if days <= 1 else score * .5 if days > 7 else score
            if score >= 0.58:
                ticket.similarity = score
                matches.append(ticket)
        return sorted(matches, key=lambda item: item.similarity, reverse=True)[:5]

    def add_endorsement(self, user_id):
        """Add one resident's confirmation without creating another admin ticket."""
        if self.user_id == user_id:
            return False
        result = Database.execute(
            "INSERT IGNORE INTO ticket_endorsements (ticket_id, user_id) VALUES (%s, %s)",
            (self.id, user_id),
        )
        if result:
            Database.execute("UPDATE tickets SET updated_at = NOW() WHERE id = %s", (self.id,))
        return bool(result)

    @classmethod
    def create(cls, user_id, category, subject, description, incident_location=None, incident_date=None):
        new_id = Database.execute(
            "INSERT INTO tickets (user_id, category, subject, description, incident_location, incident_date, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, NOW())",
            (user_id, category, subject, description, incident_location, incident_date),
        )
        return cls.get_by_id(new_id)

    def update_details(self, category, subject, description, incident_location=None, incident_date=None):
        Database.execute(
            "UPDATE tickets SET category = %s, subject = %s, description = %s, incident_location = %s, incident_date = %s, updated_at = NOW() WHERE id = %s",
            (category, subject, description, incident_location, incident_date, self.id),
        )
        self.category = category
        self.subject = subject
        self.description = description
        self.incident_location = incident_location
        self.incident_date = incident_date

    def update_status(self, new_status, resolution_note=None):
        if new_status not in self.STATUSES:
            raise ValueError("Invalid status")
        Database.execute("UPDATE tickets SET status = %s, resolution_note = %s, updated_at = NOW() WHERE id = %s", (new_status, resolution_note, self.id))
        self.status = new_status
        self.resolution_note = resolution_note

    def delete(self):
        Database.execute("DELETE FROM tickets WHERE id = %s", (self.id,))
        remaining = Database.query("SELECT COUNT(*) AS total FROM tickets", one=True)
        if remaining and remaining["total"] == 0:
            Database.execute("ALTER TABLE tickets AUTO_INCREMENT = 1")
