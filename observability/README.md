# Stack Observabilité — Infrastructure mutualisée

> Plateforme de monitoring partagée pour toutes vos apps actuelles et futures.
> Métriques (Prometheus) · Logs (EFK) · Alerting (Alertmanager) · Dashboards (Grafana/Kibana)

## Architecture

```
observability/
├── docker-compose.yml
├── prometheus/
│   ├── prometheus.yml          # Scraping via Docker SD (auto-découverte)
│   └── rules/
│       └── alerts.yml          # Alertes système génériques uniquement
├── alertmanager/
│   └── alertmanager.yml        # Slack + email (à configurer une seule fois)
├── grafana/
│   └── provisioning/
│       ├── datasources/        # Prometheus + Elasticsearch auto-configurés
│       └── dashboards/         # Dashboards système ; apps → volume grafana_dashboards
├── filebeat/
│   └── filebeat.yml            # Collecte automatique de tous les conteneurs
└── logstash/
    └── pipeline/logstash.conf
```

## Déploiement initial

```bash
# 1. Configurer alertmanager/alertmanager.yml (Slack webhook + SMTP)
# 2. Lancer la stack
docker compose up -d

# 3. Politique de rétention logs (attendre ~1 min qu'Elasticsearch démarre)
./setup-retention.sh
```

## Accès

| Service | URL | Identifiants |
|---|---|---|
| Grafana | https://grafana.devitlab.ddns.net | admin / changeme |
| Prometheus | https://prometheus.devitlab.ddns.net | — |
| Alertmanager | https://alertmanager.devitlab.ddns.net | — |
| Kibana | https://kibana.devitlab.ddns.net | — |

---

## Guide par outil

### Prometheus — Métriques

**Voir les targets (apps scrapées) :**
```
https://prometheus.devitlab.ddns.net/targets
```
Toute app avec le label `prometheus.io/scrape=true` apparaît automatiquement.

**Requêtes utiles :**
```promql
# Vérifier qu'une app répond
up{job="flask-api"}

# Taux de requêtes / seconde
rate(flask_http_request_total{job="flask-api"}[1m])

# Latence p95
histogram_quantile(0.95, sum(rate(flask_http_request_duration_seconds_bucket{job="flask-api"}[5m])) by (le))

# CPU système
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# RAM utilisée
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
```

**Recharger la config sans redémarrer :**
```bash
curl -X POST http://localhost:9090/-/reload
```

---

### Grafana — Dashboards

**Accès :** https://grafana.devitlab.ddns.net (admin / changeme)

**Dashboards recommandés à importer (via Dashboards → Import → ID) :**

| Dashboard | ID Grafana |
|---|---|
| Node Exporter Full (système) | 1860 |
| Docker cAdvisor (conteneurs) | 14282 |
| Traefik | 17346 |
| Flask Exporter | 9688 |

**Dashboards par app :**
Chaque app pousse son propre dashboard via son service `monitoring-init`.
Ils apparaissent automatiquement dans **Dashboards → Browse** (rechargement toutes les 30s).

**Créer une alerte visuelle :**
1. Ouvrir un panel → Edit
2. Onglet **Alert** → New alert rule
3. Définir la condition et le receiver (Alertmanager)

---

### Alertmanager — Alerting

**Accès :** https://alertmanager.devitlab.ddns.net

**Voir les alertes actives :**
```
https://alertmanager.devitlab.ddns.net/#/alerts
```

**Silencer une alerte temporairement :**
1. Cliquer sur l'alerte → **Silence**
2. Définir la durée et un commentaire

**Routing :**
- `severity: warning` → Slack `#alertes`
- `severity: critical` → Slack + email immédiat (repeat 30 min)

**Tester l'envoi d'une alerte :**
```bash
curl -X POST http://localhost:9093/api/v2/alerts \
  -H "Content-Type: application/json" \
  -d '[{"labels":{"alertname":"TestAlerte","severity":"warning","job":"test"}}]'
```

**Chaque app apporte ses propres règles** dans `monitoring/alerts.yml`,
poussées au démarrage via le service `monitoring-init`.

---

### Kibana — Logs

**Accès :** https://kibana.devitlab.ddns.net

**Premier démarrage — créer l'index pattern :**
1. Menu → **Stack Management** → Index Patterns → Create
2. Pattern : `filebeat-*` — Time field : `@timestamp`

**Voir les logs d'une app :**
1. Menu → **Discover**
2. Filtre KQL : `container.name: "flask-api"`
3. Colonnes utiles : `@timestamp`, `message`, `log.level`

**Filtres KQL utiles :**
```kql
# Logs d'une app
container.name: "flask-api"

# Erreurs uniquement
container.name: "flask-api" AND log.level: "ERROR"

# Recherche dans le message
container.name: "flask-api" AND message: "500"

# Plusieurs apps
container.name: ("flask-api" OR "mon-autre-app")
```

**Chaque app apporte son propre dashboard Kibana** (`monitoring/kibana.ndjson`),
importé automatiquement via le service `monitoring-init`.

---

## Brancher une nouvelle app

Aucune modification de cette stack. Dans chaque app, ajouter :

### 1. Labels Docker (métriques + Traefik)

```yaml
labels:
  - traefik.enable=true
  - traefik.docker.network=traefik-net
  - prometheus.io/scrape=true
  - prometheus.io/port=<port>
  - prometheus.io/path=/metrics
```

### 2. Réseau monitoring

```yaml
networks:
  monitoring:
    external: true
    name: observability_monitoring
```

### 3. Dossier monitoring/ dans l'app

```
mon-app/monitoring/
├── alerts.yml        # règles Prometheus
├── dashboard.json    # dashboard Grafana
└── kibana.ndjson     # saved objects Kibana
```

### 4. Service monitoring-init

```yaml
monitoring-init:
  image: alpine/curl
  restart: "no"
  volumes:
    - ./monitoring/alerts.yml:/tmp/alerts.yml:ro
    - ./monitoring/dashboard.json:/tmp/dashboard.json:ro
    - ./monitoring/kibana.ndjson:/tmp/kibana.ndjson:ro
    - prometheus_rules:/prometheus_rules
    - grafana_dashboards:/grafana_dashboards
  command: >
    sh -c "
      cp /tmp/alerts.yml /prometheus_rules/mon-app.yml &&
      cp /tmp/dashboard.json /grafana_dashboards/mon-app.json &&
      sleep 5 &&
      curl -s -X POST http://prometheus:9090/-/reload &&
      curl -s -X POST http://kibana:5601/api/saved_objects/_import?overwrite=true
        -H 'kbn-xsrf: true' -F file=@/tmp/kibana.ndjson
    "
  networks:
    - monitoring
```

> Voir **flask-api/** comme exemple de référence complet.

---

## Debug

```bash
# Logs des services
docker logs -f prometheus
docker logs -f elasticsearch
docker logs -f filebeat

# Targets Prometheus
curl http://localhost:9090/api/v1/targets

# Index Elasticsearch
curl http://localhost:9200/_cat/indices?v

# Alertes actives
curl http://localhost:9093/api/v2/alerts
```

## RAM estimée

~2 à 2,5 Go (Elasticsearch limité à 1 Go, Logstash 256 Mo heap).
