# Task API — Demo App

API RESTful de gestion de tâches construite avec Flask.  
Supervisée par **Uptime Kuma** (monitoring) et **Dozzle** (logs).

---

## Stack technique

| Composant | Technologie |
|---|---|
| Framework | Flask 3.0 |
| Base de données | SQLite |
| Validation | Marshmallow + marshmallow-sqlalchemy |
| Documentation | Swagger UI (`/apidocs`) |
| Métriques | prometheus-flask-exporter (`/metrics`) |
| Logs | python-json-logger (JSON structuré) |
| Serveur WSGI | Gunicorn |

---

## Prérequis

- Python 3.12+
- Docker + Docker Compose Plugin

---

## Lancer en local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 wsgi.py
```

API disponible sur **http://localhost:5000**

---

## Lancer avec Docker (stack complète)

```bash
# Depuis la racine du projet
docker compose up -d

# Vérifier les logs
docker compose logs -f task-api
```

---

## Endpoints

### Santé — surveillé par Uptime Kuma

```
GET /health
```

```json
{
  "status": "ok",
  "service": "task-api",
  "version": "1.0.0",
  "environment": "production",
  "uptime_seconds": 142.3,
  "timestamp": "2026-06-14T10:00:00+00:00",
  "dependencies": { "database": "ok" }
}
```

---

### Documentation interactive

```
GET /apidocs
```

Swagger UI avec tous les endpoints, schémas et exemples.

---

### Métriques Prometheus

```
GET /metrics
```

---

### Tâches

#### Lister

```
GET /api/v1/tasks?status=pending&priority=high&page=1&per_page=20
```

| Paramètre | Valeurs possibles | Défaut |
|---|---|---|
| `status` | `pending` `in_progress` `done` `cancelled` | — |
| `priority` | `low` `medium` `high` `critical` | — |
| `page` | — | `1` |
| `per_page` | max `100` | `20` |

**Réponse**

```json
{
  "data": [
    {
      "id": 1,
      "title": "Déployer la stack",
      "status": "in_progress",
      "priority": "high",
      "created_at": "2026-06-14T09:00:00+00:00",
      "updated_at": "2026-06-14T09:30:00+00:00"
    }
  ],
  "meta": { "total": 1, "page": 1, "per_page": 20, "pages": 1 }
}
```

---

#### Créer

```
POST /api/v1/tasks
Content-Type: application/json
```

```json
{ "title": "Déployer la stack", "priority": "high" }
```

Seul `title` est obligatoire. `status` = `pending`, `priority` = `medium` par défaut.

**Réponse** `201 Created`

---

#### Récupérer

```
GET /api/v1/tasks/{id}
```

---

#### Remplacer (PUT)

```
PUT /api/v1/tasks/{id}
```

Remplace tous les champs. `title` obligatoire.

---

#### Modifier partiellement (PATCH)

```
PATCH /api/v1/tasks/{id}
Content-Type: application/json
```

```json
{ "status": "done" }
```

---

#### Supprimer

```
DELETE /api/v1/tasks/{id}
```

**Réponse** `204 No Content`

---

#### Statistiques

```
GET /api/v1/stats
```

```json
{
  "total": 42,
  "by_status": { "pending": 15, "in_progress": 8, "done": 17, "cancelled": 2 },
  "by_priority": { "low": 5, "medium": 20, "high": 14, "critical": 3 }
}
```

---

## Codes de retour

| Code | Signification |
|---|---|
| `200` | Succès |
| `201` | Ressource créée |
| `204` | Suppression réussie |
| `400` | Corps JSON manquant |
| `404` | Ressource introuvable |
| `422` | Données invalides |
| `500` | Erreur interne |

---

## Exemples curl

```bash
# Créer une tâche
curl -s -X POST http://localhost:5000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Ma tâche","priority":"high"}' | jq

# Lister les tâches critiques
curl -s "http://localhost:5000/api/v1/tasks?priority=critical" | jq

# Passer à "done"
curl -s -X PATCH http://localhost:5000/api/v1/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"status":"done"}' | jq

# Statistiques
curl -s http://localhost:5000/api/v1/stats | jq

# Santé
curl -s http://localhost:5000/health | jq
```

---

## Tests

```bash
pytest tests/ -v
```

Les tests utilisent une base SQLite en mémoire, aucune dépendance externe requise.

---

## Générer de la charge

```bash
# Depuis la racine du projet
python3 demo-app/load_test.py --duration 120 --rps 2

# Depuis le dossier demo-app
python3 load_test.py --duration 120 --rps 2

# Serveur distant
API_URL=http://mon-serveur:5000 python3 load_test.py
```

Les logs apparaissent en temps réel dans **Dozzle**.  
Le temps de réponse est visible dans **Uptime Kuma**.

---

## Logs

Chaque action émet un log JSON structuré visible dans Dozzle :

```json
{
  "timestamp": "2026-06-14T10:00:00Z",
  "level": "INFO",
  "name": "app.routes.tasks",
  "message": "task_created",
  "task_id": 42,
  "priority": "high"
}
```

---

## Structure

```
demo-app/
├── app/
│   ├── __init__.py        ← factory create_app()
│   ├── config.py          ← variables d'environnement
│   ├── database.py        ← SQLAlchemy
│   ├── models.py          ← modèle Task
│   ├── schemas.py         ← validation Marshmallow
│   ├── telemetry.py       ← logs JSON + métriques Prometheus
│   └── routes/
│       ├── health.py      ← GET /health
│       ├── tasks.py       ← CRUD + stats
│       └── docs.py        ← GET /apidocs + /swagger.json
├── tests/
│   ├── conftest.py
│   └── test_tasks.py      ← 28 tests
├── wsgi.py
├── Dockerfile
├── docker-compose.yml
├── load_test.py
├── requirements.txt
└── .env.example
```
