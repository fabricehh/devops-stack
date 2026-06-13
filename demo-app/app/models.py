from datetime import datetime, timezone
from app.database import db

TASK_STATUSES = ("pending", "in_progress", "done", "cancelled")
TASK_PRIORITIES = ("low", "medium", "high", "critical")


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.Enum(*TASK_STATUSES, name="task_status"),
        nullable=False,
        default="pending",
    )
    priority = db.Column(
        db.Enum(*TASK_PRIORITIES, name="task_priority"),
        nullable=False,
        default="medium",
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<Task {self.id} {self.title!r} [{self.status}/{self.priority}]>"
