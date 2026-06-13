import logging

from flask import Blueprint, jsonify, request
from marshmallow import ValidationError
from sqlalchemy import func

from app.database import db
from app.models import Task, TASK_STATUSES, TASK_PRIORITIES
from app.schemas import task_schema, tasks_schema, task_patch_schema

logger = logging.getLogger(__name__)
tasks_bp = Blueprint("tasks", __name__, url_prefix="/api/v1")


def _paginate(query):
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    return query.paginate(page=page, per_page=per_page, error_out=False)


# ─── Collection ──────────────────────────────────────────────────────────────

@tasks_bp.get("/tasks")
def list_tasks():
    """
    Lister les tâches
    ---
    tags:
      - Tâches
    parameters:
      - {name: status,   in: query, type: string, enum: [pending, in_progress, done, cancelled]}
      - {name: priority, in: query, type: string, enum: [low, medium, high, critical]}
      - {name: page,     in: query, type: integer, default: 1}
      - {name: per_page, in: query, type: integer, default: 20}
    responses:
      200:
        description: Liste paginée de tâches
        schema:
          properties:
            data:
              type: array
              items: {$ref: '#/definitions/Task'}
            meta:
              type: object
              properties:
                total:    {type: integer}
                page:     {type: integer}
                per_page: {type: integer}
                pages:    {type: integer}
    """
    query = Task.query.order_by(Task.created_at.desc())

    if status := request.args.get("status"):
        if status not in TASK_STATUSES:
            return jsonify({"error": f"Statut invalide. Valeurs acceptées : {TASK_STATUSES}"}), 400
        query = query.filter(Task.status == status)

    if priority := request.args.get("priority"):
        if priority not in TASK_PRIORITIES:
            return jsonify({"error": f"Priorité invalide. Valeurs acceptées : {TASK_PRIORITIES}"}), 400
        query = query.filter(Task.priority == priority)

    page = _paginate(query)
    logger.info(
        "list_tasks",
        extra={"total": page.total, "page": page.page, "status": request.args.get("status")},
    )
    return jsonify({
        "data": tasks_schema.dump(page.items),
        "meta": {
            "total": page.total,
            "page": page.page,
            "per_page": page.per_page,
            "pages": page.pages,
        },
    })


@tasks_bp.post("/tasks")
def create_task():
    """
    Créer une tâche
    ---
    tags:
      - Tâches
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/TaskInput'
    responses:
      201:
        description: Tâche créée
        schema:
          $ref: '#/definitions/Task'
      400:
        description: Corps JSON manquant
      422:
        description: Données invalides
    definitions:
      TaskInput:
        type: object
        required: [title]
        properties:
          title:       {type: string, example: "Configurer Prometheus", maxLength: 200}
          description: {type: string, example: "Ajouter les scrape configs"}
          status:      {type: string, enum: [pending, in_progress, done, cancelled], default: pending}
          priority:    {type: string, enum: [low, medium, high, critical], default: medium}
      Task:
        type: object
        properties:
          id:          {type: integer}
          title:       {type: string}
          description: {type: string}
          status:      {type: string}
          priority:    {type: string}
          created_at:  {type: string, format: date-time}
          updated_at:  {type: string, format: date-time}
    """
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Corps JSON requis"}), 400

    try:
        task = task_schema.load(body, session=db.session)
    except ValidationError as err:
        return jsonify({"error": "Données invalides", "details": err.messages}), 422

    db.session.add(task)
    db.session.commit()
    logger.info("task_created", extra={"task_id": task.id, "priority": task.priority})
    return jsonify(task_schema.dump(task)), 201


# ─── Ressource unique ─────────────────────────────────────────────────────────

@tasks_bp.get("/tasks/<int:task_id>")
def get_task(task_id):
    """
    Récupérer une tâche
    ---
    tags:
      - Tâches
    parameters:
      - {name: task_id, in: path, type: integer, required: true}
    responses:
      200:
        description: Tâche trouvée
        schema:
          $ref: '#/definitions/Task'
      404:
        description: Tâche introuvable
    """
    task = db.get_or_404(Task, task_id, description=f"Tâche {task_id} introuvable.")
    return jsonify(task_schema.dump(task))


@tasks_bp.put("/tasks/<int:task_id>")
def update_task(task_id):
    """
    Remplacer une tâche (PUT complet)
    ---
    tags:
      - Tâches
    parameters:
      - {name: task_id, in: path, type: integer, required: true}
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/TaskInput'
    responses:
      200:
        description: Tâche mise à jour
        schema:
          $ref: '#/definitions/Task'
      404:
        description: Tâche introuvable
      422:
        description: Données invalides
    """
    task = db.get_or_404(Task, task_id)
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Corps JSON requis"}), 400

    try:
        task = task_schema.load(body, instance=task, session=db.session)
    except ValidationError as err:
        return jsonify({"error": "Données invalides", "details": err.messages}), 422

    db.session.commit()
    logger.info("task_updated", extra={"task_id": task.id, "status": task.status})
    return jsonify(task_schema.dump(task))


@tasks_bp.patch("/tasks/<int:task_id>")
def patch_task(task_id):
    """
    Mise à jour partielle d'une tâche (PATCH)
    ---
    tags:
      - Tâches
    parameters:
      - {name: task_id, in: path, type: integer, required: true}
      - in: body
        name: body
        schema:
          type: object
          properties:
            title:       {type: string}
            description: {type: string}
            status:      {type: string, enum: [pending, in_progress, done, cancelled]}
            priority:    {type: string, enum: [low, medium, high, critical]}
    responses:
      200:
        description: Tâche mise à jour partiellement
        schema:
          $ref: '#/definitions/Task'
      404:
        description: Tâche introuvable
    """
    task = db.get_or_404(Task, task_id)
    body = request.get_json(silent=True) or {}

    try:
        task = task_patch_schema.load(body, instance=task, session=db.session)
    except ValidationError as err:
        return jsonify({"error": "Données invalides", "details": err.messages}), 422

    db.session.commit()
    logger.info("task_patched", extra={"task_id": task.id})
    return jsonify(task_schema.dump(task))


@tasks_bp.delete("/tasks/<int:task_id>")
def delete_task(task_id):
    """
    Supprimer une tâche
    ---
    tags:
      - Tâches
    parameters:
      - {name: task_id, in: path, type: integer, required: true}
    responses:
      204:
        description: Tâche supprimée
      404:
        description: Tâche introuvable
    """
    task = db.get_or_404(Task, task_id)
    db.session.delete(task)
    db.session.commit()
    logger.info("task_deleted", extra={"task_id": task_id})
    return "", 204


# ─── Statistiques ─────────────────────────────────────────────────────────────

@tasks_bp.get("/stats")
def get_stats():
    """
    Statistiques agrégées des tâches
    ---
    tags:
      - Statistiques
    responses:
      200:
        description: Compteurs par statut et par priorité
        schema:
          properties:
            total:       {type: integer}
            by_status:   {type: object}
            by_priority: {type: object}
    """
    by_status = dict(
        db.session.execute(
            db.select(Task.status, func.count(Task.id)).group_by(Task.status)
        ).all()
    )
    by_priority = dict(
        db.session.execute(
            db.select(Task.priority, func.count(Task.id)).group_by(Task.priority)
        ).all()
    )
    return jsonify({
        "total": sum(by_status.values()),
        "by_status": by_status,
        "by_priority": by_priority,
    })
