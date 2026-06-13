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
curl https://flask-api.devitlab.ddns.net            # → {"hello": "world"}
curl https://flask-api.devitlab.ddns.net/metrics    # → métriques Prometheus

# Générer du trafic pour les dashboards
for i in $(seq 1 50); do curl -s https://api.devitlab.ddns.net > /dev/null; done
```

Logs dans Kibana : filtre `container.name: "flask-api"`.

## Logs

```bash
# Suivre les logs en temps réel
docker logs -f flask-api

# Dernières 100 lignes
docker logs --tail 100 flask-api

# Logs depuis une date
docker logs --since 1h flask-api

# Logs avec horodatage
docker logs -t flask-api
```
