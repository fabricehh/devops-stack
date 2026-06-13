#!/usr/bin/env python3
"""
Générateur de charge — Task API

Simule du trafic réaliste pour alimenter les dashboards Grafana.

Usage:
    python load_test.py                        # 60s, 5 req/s
    python load_test.py --duration 120 --rps 10
    API_URL=http://mon-serveur:5000 python load_test.py
"""
import argparse
import os
import random
import time

import requests

BASE_URL = os.getenv("API_URL", "http://localhost:5000")
SESSION = requests.Session()

TITLES = [
    "Configurer Prometheus", "Déployer Grafana", "Ajouter alertes CPU",
    "Intégrer Loki", "Tester Tempo", "Mettre à jour cAdvisor",
    "Documenter l'API", "Revoir les dashboards", "Former l'équipe",
    "Mettre en place CI/CD", "Optimiser les requêtes", "Auditer la sécurité",
]
STATUSES = ["pending", "in_progress", "done", "cancelled"]
PRIORITIES = ["low", "medium", "high", "critical"]

task_ids: list[int] = []


def _log(method: str, path: str, status: int, elapsed_ms: float) -> None:
    color = "\033[32m" if status < 400 else "\033[31m"
    reset = "\033[0m"
    print(f"{color}{method:6} {path:35} → {status}  ({elapsed_ms:.0f}ms){reset}")


def _call(method: str, path: str, **kwargs) -> requests.Response | None:
    url = f"{BASE_URL}{path}"
    try:
        r = SESSION.request(method, url, timeout=5, **kwargs)
        _log(method, path, r.status_code, r.elapsed.total_seconds() * 1000)
        return r
    except requests.RequestException as e:
        print(f"\033[33mERR  {path}: {e}\033[0m")
        return None


def create_task() -> None:
    payload = {
        "title": random.choice(TITLES) + f" #{random.randint(1, 999)}",
        "description": "Créé par le générateur de charge." if random.random() > 0.5 else None,
        "status": random.choice(STATUSES),
        "priority": random.choice(PRIORITIES),
    }
    r = _call("POST", "/api/v1/tasks", json=payload)
    if r and r.status_code == 201:
        task_ids.append(r.json()["id"])


def list_tasks() -> None:
    filters = random.choice([
        "",
        f"?status={random.choice(STATUSES)}",
        f"?priority={random.choice(PRIORITIES)}",
        "?page=1&per_page=5",
    ])
    _call("GET", f"/api/v1/tasks{filters}")


def get_task() -> None:
    if not task_ids:
        return
    _call("GET", f"/api/v1/tasks/{random.choice(task_ids)}")


def patch_task() -> None:
    if not task_ids:
        return
    _call("PATCH", f"/api/v1/tasks/{random.choice(task_ids)}", json={
        "status": random.choice(STATUSES),
    })


def delete_task() -> None:
    if not task_ids:
        return
    tid = random.choice(task_ids)
    r = _call("DELETE", f"/api/v1/tasks/{tid}")
    if r and r.status_code == 204:
        task_ids.remove(tid)


def get_stats() -> None:
    _call("GET", "/api/v1/stats")


def check_health() -> None:
    _call("GET", "/health")


# Pondération des opérations pour simuler un trafic réaliste
OPERATIONS = [
    (list_tasks,   35),
    (get_task,     25),
    (create_task,  20),
    (patch_task,   12),
    (get_stats,     5),
    (delete_task,   2),
    (check_health,  1),
]


def run(duration: int = 60, rps: float = 5.0) -> None:
    ops, weights = zip(*OPERATIONS)
    total = sum(weights)
    cumulative = []
    s = 0
    for w in weights:
        s += w
        cumulative.append(s / total)

    interval = 1.0 / rps
    end = time.monotonic() + duration

    print(f"\n▶ Générateur de charge — {BASE_URL}")
    print(f"  Durée: {duration}s   Rythme: {rps} req/s\n")

    requests_sent = 0
    while time.monotonic() < end:
        r = random.random()
        for i, threshold in enumerate(cumulative):
            if r <= threshold:
                ops[i]()
                break
        requests_sent += 1
        time.sleep(interval)

    print(f"\n✔ {requests_sent} requêtes envoyées en {duration}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Générateur de charge Task API")
    parser.add_argument("--duration", type=int, default=60, help="Durée en secondes")
    parser.add_argument("--rps", type=float, default=5.0, help="Requêtes par seconde")
    args = parser.parse_args()
    run(duration=args.duration, rps=args.rps)
