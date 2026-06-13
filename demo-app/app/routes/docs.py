from flask import Blueprint, jsonify

docs_bp = Blueprint("docs", __name__)

_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "Task API",
        "version": "1.0.0",
        "description": (
            "API RESTful de gestion de tâches.\n\n"
            "Démo de la plateforme observabilité : métriques Prometheus, "
            "logs Loki et traces Tempo via OpenTelemetry."
        ),
    },
    "tags": [
        {"name": "Santé",        "description": "État de l'application"},
        {"name": "Tâches",       "description": "CRUD des tâches"},
        {"name": "Statistiques", "description": "Agrégats"},
    ],
    "components": {
        "schemas": {
            "Task": {
                "type": "object",
                "properties": {
                    "id":          {"type": "integer", "example": 1},
                    "title":       {"type": "string",  "example": "Configurer Prometheus"},
                    "description": {"type": "string",  "example": "Ajouter les scrape configs", "nullable": True},
                    "status":      {"type": "string",  "enum": ["pending", "in_progress", "done", "cancelled"]},
                    "priority":    {"type": "string",  "enum": ["low", "medium", "high", "critical"]},
                    "created_at":  {"type": "string",  "format": "date-time"},
                    "updated_at":  {"type": "string",  "format": "date-time"},
                },
            },
            "TaskInput": {
                "type": "object",
                "required": ["title"],
                "properties": {
                    "title":       {"type": "string", "maxLength": 200, "example": "Configurer Prometheus"},
                    "description": {"type": "string", "example": "Ajouter les scrape configs"},
                    "status":      {"type": "string", "enum": ["pending", "in_progress", "done", "cancelled"], "default": "pending"},
                    "priority":    {"type": "string", "enum": ["low", "medium", "high", "critical"],           "default": "medium"},
                },
            },
            "TaskPatch": {
                "type": "object",
                "properties": {
                    "title":       {"type": "string", "maxLength": 200},
                    "description": {"type": "string"},
                    "status":      {"type": "string", "enum": ["pending", "in_progress", "done", "cancelled"]},
                    "priority":    {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                },
            },
            "Error": {
                "type": "object",
                "properties": {
                    "error":   {"type": "string"},
                    "details": {"type": "object"},
                },
            },
            "Pagination": {
                "type": "object",
                "properties": {
                    "total":    {"type": "integer"},
                    "page":     {"type": "integer"},
                    "per_page": {"type": "integer"},
                    "pages":    {"type": "integer"},
                },
            },
        }
    },
    "paths": {
        "/health": {
            "get": {
                "tags": ["Santé"],
                "summary": "Santé de l'application",
                "responses": {
                    "200": {
                        "description": "Application opérationnelle",
                        "content": {"application/json": {"schema": {
                            "type": "object",
                            "properties": {
                                "status":         {"type": "string", "example": "ok"},
                                "service":        {"type": "string"},
                                "version":        {"type": "string"},
                                "environment":    {"type": "string"},
                                "uptime_seconds": {"type": "number"},
                                "timestamp":      {"type": "string", "format": "date-time"},
                                "dependencies":   {"type": "object"},
                            },
                        }}},
                    },
                    "503": {"description": "Base de données inaccessible"},
                },
            }
        },
        "/api/v1/tasks": {
            "get": {
                "tags": ["Tâches"],
                "summary": "Lister les tâches",
                "parameters": [
                    {"name": "status",   "in": "query", "schema": {"type": "string", "enum": ["pending", "in_progress", "done", "cancelled"]}},
                    {"name": "priority", "in": "query", "schema": {"type": "string", "enum": ["low", "medium", "high", "critical"]}},
                    {"name": "page",     "in": "query", "schema": {"type": "integer", "default": 1}},
                    {"name": "per_page", "in": "query", "schema": {"type": "integer", "default": 20}},
                ],
                "responses": {
                    "200": {
                        "description": "Liste paginée",
                        "content": {"application/json": {"schema": {
                            "type": "object",
                            "properties": {
                                "data": {"type": "array", "items": {"$ref": "#/components/schemas/Task"}},
                                "meta": {"$ref": "#/components/schemas/Pagination"},
                            },
                        }}},
                    }
                },
            },
            "post": {
                "tags": ["Tâches"],
                "summary": "Créer une tâche",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/TaskInput"}}},
                },
                "responses": {
                    "201": {"description": "Tâche créée",     "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Task"}}}},
                    "400": {"description": "Corps JSON manquant"},
                    "422": {"description": "Données invalides", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                },
            },
        },
        "/api/v1/tasks/{task_id}": {
            "parameters": [
                {"name": "task_id", "in": "path", "required": True, "schema": {"type": "integer"}}
            ],
            "get": {
                "tags": ["Tâches"],
                "summary": "Récupérer une tâche",
                "responses": {
                    "200": {"description": "Tâche trouvée",    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Task"}}}},
                    "404": {"description": "Tâche introuvable"},
                },
            },
            "put": {
                "tags": ["Tâches"],
                "summary": "Remplacer une tâche (PUT complet)",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/TaskInput"}}},
                },
                "responses": {
                    "200": {"description": "Tâche mise à jour", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Task"}}}},
                    "404": {"description": "Tâche introuvable"},
                    "422": {"description": "Données invalides"},
                },
            },
            "patch": {
                "tags": ["Tâches"],
                "summary": "Mise à jour partielle (PATCH)",
                "requestBody": {
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/TaskPatch"}}},
                },
                "responses": {
                    "200": {"description": "Tâche mise à jour", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Task"}}}},
                    "404": {"description": "Tâche introuvable"},
                },
            },
            "delete": {
                "tags": ["Tâches"],
                "summary": "Supprimer une tâche",
                "responses": {
                    "204": {"description": "Tâche supprimée"},
                    "404": {"description": "Tâche introuvable"},
                },
            },
        },
        "/api/v1/stats": {
            "get": {
                "tags": ["Statistiques"],
                "summary": "Statistiques agrégées",
                "responses": {
                    "200": {
                        "description": "Compteurs par statut et priorité",
                        "content": {"application/json": {"schema": {
                            "type": "object",
                            "properties": {
                                "total":       {"type": "integer"},
                                "by_status":   {"type": "object"},
                                "by_priority": {"type": "object"},
                            },
                        }}},
                    }
                },
            }
        },
    },
}

_SWAGGER_UI_HTML = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Task API — Swagger UI</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css"/>
  <style>body { margin: 0; }</style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    SwaggerUIBundle({
      url: "/swagger.json",
      dom_id: "#swagger-ui",
      deepLinking: true,
      presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
      layout: "BaseLayout",
      tryItOutEnabled: true,
    });
  </script>
</body>
</html>"""


@docs_bp.get("/swagger.json")
def swagger_json():
    return jsonify(_SPEC)


@docs_bp.get("/apidocs")
def swagger_ui():
    return _SWAGGER_UI_HTML, 200, {"Content-Type": "text/html"}
