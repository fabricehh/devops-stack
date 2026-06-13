import pytest


# ─── Santé ────────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "ok"
        assert data["dependencies"]["database"] == "ok"
        assert "uptime_seconds" in data


# ─── Liste ────────────────────────────────────────────────────────────────────

class TestListTasks:
    def test_list_empty(self, client):
        r = client.get("/api/v1/tasks")
        assert r.status_code == 200
        body = r.get_json()
        assert body["data"] == []
        assert body["meta"]["total"] == 0

    def test_list_with_tasks(self, client, task):
        r = client.get("/api/v1/tasks")
        assert r.status_code == 200
        assert r.get_json()["meta"]["total"] == 1

    def test_filter_by_status(self, client, task):
        r = client.get("/api/v1/tasks?status=pending")
        assert r.status_code == 200
        assert len(r.get_json()["data"]) == 1

        r = client.get("/api/v1/tasks?status=done")
        assert r.status_code == 200
        assert len(r.get_json()["data"]) == 0

    def test_filter_by_priority(self, client, task):
        r = client.get("/api/v1/tasks?priority=high")
        assert r.status_code == 200
        assert len(r.get_json()["data"]) == 1

    def test_invalid_status_filter(self, client):
        r = client.get("/api/v1/tasks?status=invalid")
        assert r.status_code == 400

    def test_pagination(self, client, app):
        from app.database import db
        from app.models import Task
        with app.app_context():
            for i in range(5):
                db.session.add(Task(title=f"Task {i}"))
            db.session.commit()

        r = client.get("/api/v1/tasks?page=1&per_page=3")
        body = r.get_json()
        assert len(body["data"]) == 3
        assert body["meta"]["pages"] == 2
        assert body["meta"]["total"] == 5


# ─── Création ─────────────────────────────────────────────────────────────────

class TestCreateTask:
    def test_create_minimal(self, client):
        r = client.post("/api/v1/tasks", json={"title": "Ma tâche"})
        assert r.status_code == 201
        data = r.get_json()
        assert data["title"] == "Ma tâche"
        assert data["status"] == "pending"
        assert data["priority"] == "medium"
        assert "id" in data
        assert "created_at" in data

    def test_create_full(self, client):
        payload = {
            "title": "Configurer Grafana",
            "description": "Ajouter les datasources",
            "status": "in_progress",
            "priority": "high",
        }
        r = client.post("/api/v1/tasks", json=payload)
        assert r.status_code == 201
        data = r.get_json()
        assert data["status"] == "in_progress"
        assert data["priority"] == "high"
        assert data["description"] == "Ajouter les datasources"

    def test_create_missing_title(self, client):
        r = client.post("/api/v1/tasks", json={"priority": "low"})
        assert r.status_code == 422
        assert "details" in r.get_json()

    def test_create_invalid_status(self, client):
        r = client.post("/api/v1/tasks", json={"title": "X", "status": "invalid"})
        assert r.status_code == 422

    def test_create_no_body(self, client):
        r = client.post("/api/v1/tasks", content_type="application/json")
        assert r.status_code == 400

    def test_create_title_too_long(self, client):
        r = client.post("/api/v1/tasks", json={"title": "x" * 201})
        assert r.status_code == 422


# ─── Récupération ─────────────────────────────────────────────────────────────

class TestGetTask:
    def test_get_existing(self, client, task):
        r = client.get(f"/api/v1/tasks/{task['id']}")
        assert r.status_code == 200
        assert r.get_json()["id"] == task["id"]

    def test_get_not_found(self, client):
        r = client.get("/api/v1/tasks/9999")
        assert r.status_code == 404


# ─── Mise à jour complète (PUT) ───────────────────────────────────────────────

class TestUpdateTask:
    def test_put_updates_all_fields(self, client, task):
        r = client.put(f"/api/v1/tasks/{task['id']}", json={
            "title": "Titre modifié",
            "status": "done",
            "priority": "low",
        })
        assert r.status_code == 200
        data = r.get_json()
        assert data["title"] == "Titre modifié"
        assert data["status"] == "done"
        assert data["priority"] == "low"

    def test_put_not_found(self, client):
        r = client.put("/api/v1/tasks/9999", json={"title": "X"})
        assert r.status_code == 404

    def test_put_invalid_data(self, client, task):
        r = client.put(f"/api/v1/tasks/{task['id']}", json={"title": ""})
        assert r.status_code == 422


# ─── Mise à jour partielle (PATCH) ───────────────────────────────────────────

class TestPatchTask:
    def test_patch_status_only(self, client, task):
        r = client.patch(f"/api/v1/tasks/{task['id']}", json={"status": "done"})
        assert r.status_code == 200
        assert r.get_json()["status"] == "done"
        assert r.get_json()["title"] == task["title"]  # inchangé

    def test_patch_priority_only(self, client, task):
        r = client.patch(f"/api/v1/tasks/{task['id']}", json={"priority": "critical"})
        assert r.status_code == 200
        assert r.get_json()["priority"] == "critical"

    def test_patch_empty_body(self, client, task):
        r = client.patch(f"/api/v1/tasks/{task['id']}", json={})
        assert r.status_code == 200  # rien à changer, réponse valide

    def test_patch_not_found(self, client):
        r = client.patch("/api/v1/tasks/9999", json={"status": "done"})
        assert r.status_code == 404


# ─── Suppression ─────────────────────────────────────────────────────────────

class TestDeleteTask:
    def test_delete_existing(self, client, task):
        r = client.delete(f"/api/v1/tasks/{task['id']}")
        assert r.status_code == 204
        assert r.data == b""

        # Vérifier que la ressource a disparu
        r2 = client.get(f"/api/v1/tasks/{task['id']}")
        assert r2.status_code == 404

    def test_delete_not_found(self, client):
        r = client.delete("/api/v1/tasks/9999")
        assert r.status_code == 404


# ─── Statistiques ─────────────────────────────────────────────────────────────

class TestStats:
    def test_stats_empty(self, client):
        r = client.get("/api/v1/stats")
        assert r.status_code == 200
        assert r.get_json()["total"] == 0

    def test_stats_with_data(self, client, app):
        from app.database import db
        from app.models import Task
        with app.app_context():
            db.session.add(Task(title="A", status="pending", priority="low"))
            db.session.add(Task(title="B", status="done", priority="high"))
            db.session.add(Task(title="C", status="done", priority="high"))
            db.session.commit()

        r = client.get("/api/v1/stats")
        data = r.get_json()
        assert data["total"] == 3
        assert data["by_status"]["done"] == 2
        assert data["by_status"]["pending"] == 1
        assert data["by_priority"]["high"] == 2
