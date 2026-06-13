# Guide d'utilisation — Stack Observabilité

---

## Prometheus — Métriques

**URL :** https://prometheus.devitlab.ddns.net

### Voir les targets actives

```
https://prometheus.devitlab.ddns.net/targets
```

Toute app avec le label `prometheus.io/scrape=true` apparaît automatiquement.
Statuts : `UP` · `DOWN` · `UNKNOWN`

### Onglets utiles

| Onglet | Usage |
|---|---|
| **Graph** | Exécuter des requêtes PromQL |
| **Alerts** | État des règles (firing / pending / inactive) |
| **Status > Targets** | Santé de tous les endpoints scrapés |
| **Status > Rules** | Toutes les règles d'alerte chargées |

### Requêtes PromQL essentielles

```promql
# Santé d'une app
up{job="flask-api"}

# Taux de requêtes / seconde
rate(flask_http_request_total{job="flask-api"}[1m])

# Taux d'erreurs 5xx
rate(flask_http_request_total{job="flask-api", status=~"5.."}[1m])

# Latence p95
histogram_quantile(0.95,
  sum(rate(flask_http_request_duration_seconds_bucket{job="flask-api"}[5m])) by (le)
)

# CPU système (%)
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# RAM utilisée (%)
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Disque utilisé (%)
(1 - (node_filesystem_avail_bytes{fstype!="tmpfs"} / node_filesystem_size_bytes)) * 100

# CPU par conteneur
rate(container_cpu_usage_seconds_total{name!=""}[1m]) * 100

# RAM par conteneur
container_memory_usage_bytes{name!=""}
```

### Opérations courantes

```bash
# Recharger la config
curl -X POST http://localhost:9090/-/reload

# Targets en CLI
curl -s http://localhost:9090/api/v1/targets | python3 -m json.tool

# Alertes actives
curl -s http://localhost:9090/api/v1/alerts | python3 -m json.tool
```

---

## Grafana — Dashboards

**URL :** https://grafana.devitlab.ddns.net
**Identifiants :** admin / changeme

### Premier démarrage — importer les dashboards système

Menu → **Dashboards** → **Import** → saisir l'ID :

| Dashboard | ID |
|---|---|
| Node Exporter Full (système) | 1860 |
| Docker cAdvisor (conteneurs) | 14282 |
| Traefik | 17346 |
| Flask Exporter | 9688 |

### Dashboards par app

Chaque app pousse son `dashboard.json` via son service `monitoring-init`.
Ils apparaissent automatiquement dans **Dashboards → Browse** (rafraîchissement toutes les 30s).

### Explorer les métriques

1. Menu → **Explore**
2. Sélectionner la datasource **Prometheus**
3. Saisir une requête PromQL
4. Passer en vue **Table** ou **Time series**

### Créer une alerte Grafana

1. Ouvrir un panel → **Edit**
2. Onglet **Alert** → **New alert rule**
3. Définir la condition, le seuil et le contact point (Alertmanager)

### Changer le mot de passe

Menu (icône user) → **Profile** → **Change password**

---

## Alertmanager — Alerting

**URL :** https://alertmanager.devitlab.ddns.net

### Routing configuré

| Sévérité | Canal | Répétition |
|---|---|---|
| `warning` | Slack `#alertes` | toutes les 3h |
| `critical` | Slack + Email | toutes les 30 min |

### Voir les alertes actives

```
https://alertmanager.devitlab.ddns.net/#/alerts
```

### Silencer une alerte

1. Cliquer sur l'alerte → **Silence**
2. Définir la durée et un commentaire
3. Cliquer **Create**

Les silences actifs sont visibles dans l'onglet **Silences**.

### Tester l'envoi d'une alerte

```bash
curl -X POST http://localhost:9093/api/v2/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "TestAlerte",
      "severity": "warning",
      "job": "test"
    },
    "annotations": {
      "summary": "Alerte de test",
      "description": "Ceci est un test."
    }
  }]'
```

### Configurer Slack et Email

Éditer `alertmanager/alertmanager.yml` :

```yaml
receivers:
  - name: default
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/XXX/YYY/ZZZ'
        channel: '#alertes'

  - name: email-critical
    email_configs:
      - to: 'admin@mondomaine.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'mon@gmail.com'
        auth_password: 'app_password_gmail'
```

Puis recharger :

```bash
curl -X POST http://localhost:9093/-/reload
```

### Alertes par app

Chaque app porte ses propres règles dans `monitoring/alerts.yml`, poussées via `monitoring-init`.
L'Alertmanager route automatiquement selon les labels `severity` et `app`.

---

## Kibana — Logs

**URL :** https://kibana.devitlab.ddns.net

### Premier démarrage — créer l'index pattern

1. Menu → **Stack Management** → **Index Patterns** → **Create index pattern**
2. Pattern : `filebeat-*`
3. Time field : `@timestamp`
4. Valider

### Voir les logs — Discover

1. Menu → **Discover**
2. Sélectionner l'index `filebeat-*`
3. Appliquer un filtre KQL dans la barre de recherche

### Filtres KQL utiles

```kql
# Logs d'une app
container.name: "flask-api"

# Erreurs uniquement
container.name: "flask-api" AND log.level: "ERROR"

# Recherche dans le message
container.name: "flask-api" AND message: *500*

# Plusieurs apps
container.name: ("flask-api" OR "mon-autre-app")

# Plage de temps personnalisée : utiliser le sélecteur en haut à droite
```

### Colonnes recommandées dans Discover

Cliquer sur **+** à côté des champs :
- `container.name`
- `log.level`
- `message`

### Dashboards par app

Chaque app pousse ses saved objects (`kibana.ndjson`) via son service `monitoring-init`.
Ils apparaissent dans **Dashboard → Browse** après l'import.

### Créer une visualisation

1. Menu → **Visualize Library** → **Create visualization**
2. Choisir le type (Bar, Line, Pie…)
3. Sélectionner l'index `filebeat-*`
4. Configurer les axes et filtres
5. **Save** et ajouter à un dashboard

### Surveiller les index

```bash
# Lister les index Elasticsearch
curl http://localhost:9200/_cat/indices?v

# Taille des index filebeat
curl http://localhost:9200/_cat/indices/filebeat-*?v&h=index,docs.count,store.size
```
