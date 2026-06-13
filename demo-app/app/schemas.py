from marshmallow import fields, validate, EXCLUDE
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field
from app.models import Task, TASK_STATUSES, TASK_PRIORITIES


class TaskSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Task
        load_instance = True
        include_fk = True
        unknown = EXCLUDE

    id = auto_field(dump_only=True)
    title = auto_field(required=True, validate=validate.Length(min=1, max=200))
    description = auto_field(allow_none=True, load_default=None)
    status = auto_field(
        load_default="pending",
        validate=validate.OneOf(TASK_STATUSES, error="Statut invalide."),
    )
    priority = auto_field(
        load_default="medium",
        validate=validate.OneOf(TASK_PRIORITIES, error="Priorité invalide."),
    )
    created_at = auto_field(dump_only=True)
    updated_at = auto_field(dump_only=True)


task_schema = TaskSchema()
tasks_schema = TaskSchema(many=True)
task_patch_schema = TaskSchema(partial=True)
