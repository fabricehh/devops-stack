# Task API — Demo Observabilité

API RESTful de gestion de tâches construite avec Flask.  
Démontre l'intégration complète avec la stack observabilité : **Prometheus · Loki · Tempo** via **OpenTelemetry**.

---

## Stack technique

| Composant | Technologie |
|---|---|
| Framework | Flask 3.0 |
| Base de données | SQLite (dev) / PostgreSQL (prod) |
| Validation | Marshmallow + marshmallow-sqlalchemy |
| Documentation | Flasgger (Swagger UI) |
| Métriques | prometheus-flask-exporter |
| Logs | python-json-logger |
| Traces / Métriques / Logs | OpenTelemetry SDK → OTel Collector |
| Serveur WSGI | Gunicorn |

---

## Prérequis

- Python 3.12+
- Docker + Docker Compose Plugin
- Stack observabilité démarrée (`observability/docker-compose.yml`)

---

## Installation locale (sans Docker)

```bash
# 1. Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate        # Linux / Mac
.venv\Scripts\activate           # Windows

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer l'environnement
cp .env.example .env

# 4. Lancer l'application
python wsgi.py
```

L'API est disponible sur **http://localhost:5000**

> Sans `OTEL_EXPORTER_OTLP_ENDPOINT` configuré, l'app fonctionne normalement mais sans traces ni métriques OTel.

---

## Installation Docker

```bash
# Démarrer la stack observabilité d'abord
cd ../observability && docker compose up -d && cd ../demo-app

# Construire et démarrer la demo app
docker compose up -d

# Vérifier
docker compose logs -f task-api
```

L'app rejoint automatiquement le réseau `observability_monitoring` et envoie ses données à l'OTel Collector.

---

## Endpoints

### Santé

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
  "timestamp": "2026-06-13T10:00:00+00:00",
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

Expose les métriques HTTP (requêtes, latences, codes de réponse) directement scrappables par Prometheus.

---

### Tâches

#### Lister les tâches

```
GET /api/v1/tasks
```

| Paramètre | Type | Valeurs possibles | Défaut |
|---|---|---|---|
| `status` | string | `pending` `in_progress` `done` `cancelled` | — |
| `priority` | string | `low` `medium` `high` `critical` | — |
| `page` | integer | — | `1` |
| `per_page` | integer | max `100` | `20` |

**Réponse**

```json
{
  "data": [
    {
      "id": 1,
      "title": "Configurer Prometheus",
      "description": "Ajouter les scrape configs pour les app servers",
      "status": "in_progress",
      "priority": "high",
      "created_at": "2026-06-13T09:00:00+00:00",
      "updated_at": "2026-06-13T09:30:00+00:00"
    }
  ],
  "meta": {
    "total": 1,
    "page": 1,
    "per_page": 20,
    "pages": 1
  }
}
```

---

#### Créer une tâche

```
POST /api/v1/tasks
Content-Type: application/json
```

```json
{
  "title": "Configurer Prometheus",
  "description": "Ajouter les scrape configs",
  "status": "pending",
  "priority": "high"
}
```

Seul `title` est obligatoire. `status` vaut `pending` et `priority` vaut `medium` par défaut.

**Réponse** `201 Created`

```json
{
  "id": 1,
  "title": "Configurer Prometheus",
  "description": "Ajouter les scrape configs",
  "status": "pending",
  "priority": "high",
  "created_at": "2026-06-13T09:00:00+00:00",
  "updated_at": "2026-06-13T09:00:00+00:00"
}
```

---

#### Récupérer une tâche

```
GET /api/v1/tasks/{id}
```

---

#### Remplacer une tâche (PUT)

```
PUT /api/v1/tasks/{id}
Content-Type: application/json
```

Remplace tous les champs. `title` est obligatoire.

---

#### Mise à jour partielle (PATCH)

```
PATCH /api/v1/tasks/{id}
Content-Type: application/json
```

```json
{ "status": "done" }
```

Seuls les champs fournis sont modifiés.

---

#### Supprimer une tâche

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
  "by_status": {
    "pending": 15,
    "in_progress": 8,
    "done": 17,
    "cancelled": 2
  },
  "by_priority": {
    "low": 5,
    "medium": 20,
    "high": 14,
    "critical": 3
  }
}
```

---

## Codes de retour

| Code | Signification |
|---|---|
| `200` | Succès |
| `201` | Ressource créée |
| `204` | Suppression réussie (pas de corps) |
| `400` | Corps JSON manquant |
| `404` | Ressource introuvable |
| `405` | Méthode non autorisée |
| `422` | Données invalides (détail des erreurs inclus) |
| `500` | Erreur interne |

**Exemple d'erreur 422**

```json
{
  "error": "Données invalides",
  "details": {
    "title": ["Missing data for required field."],
    "status": ["Statut invalide."]
  }
}
```

---

## Exemples curl

```bash
# Créer une tâche
curl -s -X POST http://localhost:5000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Ma première tâche","priority":"high"}' | jq

# Lister les tâches urgentes en cours
curl -s "http://localhost:5000/api/v1/tasks?priority=critical&status=in_progress" | jq

# Passer une tâche à "done"
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
# Lancer tous les tests
pytest tests/ -v

# Avec couverture
pytest tests/ -v --tb=short

# Un test spécifique
pytest tests/test_tasks.py::TestCreateTask::test_create_full -v
```

Les tests utilisent une base SQLite en mémoire et désactivent OTel — aucune dépendance externe requise.

---

## Générer de la charge

Le script `load_test.py` simule du trafic réaliste pour alimenter les dashboards Grafana.

```bash
# 60 secondes à 5 req/s (défaut)
python load_test.py

# 5 minutes à 10 req/s
python load_test.py --duration 300 --rps 10

# Cibler un serveur distant
API_URL=http://srv-app-01:5000 python load_test.py --duration 120
```

---

## Observabilité

### Ce que l'app envoie automatiquement

```
Task API
   │
   │  OTLP gRPC (port 4317)
   ▼
OTel Collector
   ├── Traces  → Tempo    (chaque requête HTTP + requête SQL)
   ├── Logs    → Loki     (JSON structuré avec trace_id)
   └── Métriques → Prometheus (via endpoint /metrics + OTel)
```

### Variables d'environnement OTel

| Variable | Description | Exemple |
|---|---|---|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Adresse de l'OTel Collector | `http://otelcollector:4317` |
| `OTEL_SERVICE_NAME` | Nom du service dans Grafana | `task-api` |
| `SERVICE_VERSION` | Version affichée dans les traces | `1.0.0` |
| `DEPLOYMENT_ENVIRONMENT` | Label d'environnement | `production` |

### Format des logs

Chaque log est émis en JSON structuré :

```json
{
  "timestamp": "2026-06-13T10:00:00.123Z",
  "level": "INFO",
  "name": "app.routes.tasks",
  "message": "task_created",
  "task_id": 42,
  "priority": "high"
}
```

Le champ `trace_id` est automatiquement injecté par OTel dans chaque log, permettant la corrélation **log ↔ trace** dans Grafana.

### Dashboards Grafana

Après démarrage, l'app apparaît dans :

| Dashboard | Métriques visibles |
|---|---|
| **Applications** | Requêtes/s, latence P50/P95, taux d'erreurs, disponibilité |
| **Logs** | Tous les logs filtrables par niveau et par texte |
| **Traces** | Traces des requêtes HTTP et des requêtes SQL |
| **Docker** | CPU et RAM du container `task-api` |

---

## Structure du projet

```
demo-app/
├── app/
│   ├── __init__.py        ← factory create_app()
│   ├── config.py          ← configuration depuis les variables d'env
│   ├── database.py        ← instance SQLAlchemy
│   ├── models.py          ← modèle Task
│   ├── schemas.py         ← schémas de validation Marshmallow
│   ├── telemetry.py       ← OTel traces + métriques + logs, Prometheus
│   └── routes/
│       ├── health.py      ← GET /health
│       └── tasks.py       ← CRUD /api/v1/tasks + /api/v1/stats
├── tests/
│   ├── conftest.py        ← fixtures pytest
│   └── test_tasks.py      ← 28 tests (tous les endpoints et cas limites)
├── wsgi.py                ← entry point Gunicorn
├── Dockerfile
├── docker-compose.yml
├── load_test.py           ← générateur de charge
├── requirements.txt
└── .env.example
```

---

## Intégrer une autre application

Ce projet sert de référence. Pour intégrer votre propre application :

1. Installer le SDK OpenTelemetry de votre langage
2. Configurer `OTEL_EXPORTER_OTLP_ENDPOINT` vers l'OTel Collector
3. Émettre des logs en JSON avec les champs `level`, `service`, `message`
4. L'application apparaît automatiquement dans tous les dashboards Grafana

Voir [observability/user-guide.md](../observability/user-guide.md) pour les exemples par langage (Java, Node.js, .NET, Go).
