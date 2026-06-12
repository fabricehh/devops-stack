# 📊 Stack Observabilité — Infrastructure mutualisée

> Plateforme de monitoring partagée pour **toutes vos apps actuelles et futures**.
> Métriques (Prometheus) · Logs (EFK) · Alerting (Alertmanager) · Dashboards (Grafana/Kibana)

## Architecture

```
~/observability/
├── docker-compose.yml
├── setup-retention.sh          # Politique ILM (rétention logs 7 jours)
├── prometheus/
│   ├── prometheus.yml          # ← AJOUTEZ ICI vos nouvelles apps à scraper
│   └── rules/
│       └── alerts.yml          # ← AJOUTEZ ICI vos règles d'alerte
├── alertmanager/
│   └── alertmanager.yml        # Slack + email
├── grafana/
│   └── provisioning/
│       ├── datasources/        # Prometheus + Elasticsearch auto-configurés
│       └── dashboards/
├── filebeat/
│   └── filebeat.yml            # Collecte AUTOMATIQUE des logs de TOUS les conteneurs
└── logstash/
    └── pipeline/
        └── logstash.conf
```

## Avant de lancer

1. **alertmanager/alertmanager.yml** : remplacez le webhook Slack et les identifiants SMTP
2. **docker-compose.yml** : adaptez les domaines `*.devitlab.ddns.net` si besoin
3. Le réseau `traefik-net` doit exister : `docker network create traefik-net`

## Déploiement

```bash
docker compose up -d
docker ps --format "table {{.Names}}\t{{.Status}}"

# Rétention des logs (une seule fois, attendre ~1 min qu'ES démarre)
./setup-retention.sh
```

## Accès

| Service | URL | Identifiants |
|---------|-----|-------------|
| Grafana | https://grafana.devitlab.ddns.net | admin / changeme |
| Prometheus | https://prometheus.devitlab.ddns.net | — |
| Alertmanager | https://alertmanager.devitlab.ddns.net | — |
| Kibana | https://kibana.devitlab.ddns.net | — |

---

## 🔌 Brancher une nouvelle app (procédure standard)

### 1. Logs → automatique ✅

Filebeat collecte déjà les logs de **tous les conteneurs Docker**.
Pour des logs structurés, faites sortir du **JSON sur stdout** dans votre app.
Dans Kibana, filtrez avec `container.name: "mon-app"`.

### 2. Métriques → 2 étapes

**a)** Exposez un endpoint `/metrics` dans votre app
(ex: `prometheus-flask-exporter` en Python, `micrometer` en Java, `prom-client` en Node).

**b)** Ajoutez le job dans `prometheus/prometheus.yml` :

```yaml
  - job_name: mon-app
    static_configs:
      - targets: ['mon-app:8080']
```

Puis rechargez : `curl -X POST http://localhost:9090/-/reload`

### 3. Réseau → connecter l'app au réseau monitoring

Dans le `docker-compose.yml` de votre app :

```yaml
networks:
  monitoring:
    external: true
    name: observability_monitoring
```

### 4. Alertes → ajouter vos règles

Dans `prometheus/rules/alerts.yml`, ajoutez un groupe pour votre app
(voir le groupe `flask-api` comme modèle), puis rechargez Prometheus.

> 📦 Voir le dossier **flask-api/** (livré à côté) : app démo complète qui suit cette procédure.

---

## Dashboards Grafana à importer

| Dashboard | ID |
|-----------|----|
| Node Exporter Full | 1860 |
| Docker cAdvisor | 14282 |
| Traefik | 17346 |
| Flask exporter | 9688 |

## Debug

```bash
docker logs -f prometheus
docker logs -f elasticsearch
docker logs -f filebeat

# Targets Prometheus
curl http://localhost:9090/api/v1/targets

# Index Elasticsearch
curl http://localhost:9200/_cat/indices?v

# Recharger Prometheus après modif
curl -X POST http://localhost:9090/-/reload
```

## RAM estimée

~2 à 2,5 Go pour l'ensemble (Elasticsearch limité à 1 Go, Logstash 256 Mo heap).
