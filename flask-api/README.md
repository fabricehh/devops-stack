# 🐍 Flask API — App démo branchée sur la stack Observabilité

App exemple montrant comment brancher n'importe quelle app sur la stack mutualisée :

| Intégration | Comment |
|---|---|
| **Métriques** | `prometheus-flask-exporter` expose `/metrics` — job déjà déclaré dans `observability/prometheus/prometheus.yml` |
| **Logs** | `python-json-logger` → JSON sur stdout → collecté automatiquement par Filebeat |
| **Alertes** | Groupe `flask-api` dans `observability/prometheus/rules/alerts.yml` |
| **Réseau** | Connectée à `observability_monitoring` (externe) |

## Prérequis

La stack observability doit être lancée **avant** (elle crée le réseau `observability_monitoring`).

## Déploiement

```bash
docker compose up -d --build
```

## Tester

```bash
curl https://api.devitlab.ddns.net            # → {"hello": "world"}
curl https://api.devitlab.ddns.net/metrics    # → métriques Prometheus

# Générer du trafic pour les dashboards
for i in $(seq 1 50); do curl -s https://api.devitlab.ddns.net > /dev/null; done
```

Logs dans Kibana : filtre `container.name: "flask-api"`.
