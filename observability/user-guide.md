# Guide Utilisateur — Plateforme Observabilité

## Prérequis

| Élément | Version minimale |
|---|---|
| Docker | 24.x |
| Docker Compose Plugin | 2.x |
| Traefik | v3 (déjà déployé) |
| Domaine DNS | devitlab.ddns.net |
| Ports ouverts | 80, 443, 4317, 4318 |

---

## 1. Installation

### 1.1 Cloner le dépôt

```bash
git clone https://github.com/fabricehh/devops-stack.git
cd devops-stack/observability
```

### 1.2 Configurer les variables d'environnement

```bash
cp .env.example .env
nano .env
```

Remplir les valeurs :

```env
GF_ADMIN_USER=admin
GF_ADMIN_PASSWORD=MotDePasseSecurise

SMTP_USER=alerts@votre-domaine.com
SMTP_PASSWORD=votre-mot-de-passe

ALERT_EMAIL=ops-team@votre-domaine.com
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/VOTRE-ID
```

### 1.3 Configurer AlertManager

Éditer `alertmanager/alertmanager.yml` et remplacer les 3 placeholders :

```yaml
smtp_from: alerts@votre-domaine.com
smtp_auth_username: alerts@votre-domaine.com
smtp_auth_password: votre-mot-de-passe

url: https://outlook.office.com/webhook/VOTRE-WEBHOOK-TEAMS
to: ops-team@votre-domaine.com
```

### 1.4 Créer le réseau Traefik (si pas déjà fait)

```bash
docker network create traefik-net
```

### 1.5 Démarrer la stack

```bash
docker compose up -d
```

### 1.6 Vérifier que tous les services sont UP

```bash
docker compose ps
```

Résultat attendu :

```
NAME              STATUS
prometheus        Up
alertmanager      Up
grafana           Up
loki              Up
tempo             Up
otelcollector     Up
node-exporter     Up
cadvisor          Up
```

---

## 2. Accès aux interfaces

| Service | URL | Identifiants |
|---|---|---|
| Grafana | https://grafana.devitlab.ddns.net | admin / *voir .env* |
| Prometheus | https://prometheus.devitlab.ddns.net | — |
| AlertManager | https://alertmanager.devitlab.ddns.net | — |

---

## 3. Dashboards Grafana

Les 5 dashboards sont provisionnés automatiquement dans le dossier **Infrastructure**.

### Dashboard Infrastructure

**Chemin :** Dashboards → Infrastructure → Infrastructure

Affiche CPU, RAM, Disque et Réseau pour chaque serveur supervisé.

Seuils configurés :
- CPU / RAM > 80% → orange
- CPU / RAM > 95% → rouge
- Disque > 80% → orange, > 95% → rouge

---

### Dashboard Docker

**Chemin :** Dashboards → Infrastructure → Docker

Affiche le nombre de containers actifs/arrêtés, CPU et RAM par container.

---

### Dashboard Applications

**Chemin :** Dashboards → Infrastructure → Applications

Affiche pour chaque application :
- Requêtes / seconde
- Temps de réponse P50 / P95
- Taux d'erreurs 5xx
- Disponibilité sur 24h

> Les métriques apparaissent automatiquement dès qu'une application envoie des données via OpenTelemetry.

---

### Dashboard Logs

**Chemin :** Dashboards → Infrastructure → Logs

Affiche les logs en temps réel avec :
- Filtre par niveau (ERROR / WARNING / INFO)
- Moteur de recherche textuelle (variable **Recherche** en haut)
- Volume de logs par niveau en graphique

---

### Dashboard Traces

**Chemin :** Dashboards → Infrastructure → Traces

Affiche :
- Appels par service (spans/s)
- Latence P95 par service
- Taux d'erreurs (spans en erreur)
- Service Map (graphe des dépendances entre services)

---

## 4. Ajouter un serveur applicatif à superviser

Chaque serveur applicatif (srv-app-01, srv-app-02, …) doit avoir **Node Exporter** et **cAdvisor** installés.

### 4.1 Installer Node Exporter sur le serveur applicatif

```bash
# Sur srv-app-01
docker run -d \
  --name node-exporter \
  --restart unless-stopped \
  --pid host \
  -v /proc:/host/proc:ro \
  -v /sys:/host/sys:ro \
  -v /:/host:ro,rslave \
  prom/node-exporter:v1.8.1 \
  --path.rootfs=/host
```

### 4.2 Installer cAdvisor sur le serveur applicatif

```bash
docker run -d \
  --name cadvisor \
  --restart unless-stopped \
  --privileged \
  -v /:/rootfs:ro \
  -v /var/run:/var/run:ro \
  -v /sys:/sys:ro \
  -v /var/lib/docker:/var/lib/docker:ro \
  gcr.io/cadvisor/cadvisor:v0.49.1
```

### 4.3 Déclarer le serveur dans Prometheus

Sur **srv-observability**, créer un fichier dans `prometheus/targets/` :

```bash
# Fichier : prometheus/targets/node-exporter-srv-app-01.yml
cat > prometheus/targets/node-exporter-srv-app-01.yml << EOF
- targets: [192.168.1.101:9100]
  labels:
    instance: srv-app-01
    env: production
EOF

# Fichier : prometheus/targets/cadvisor-srv-app-01.yml
cat > prometheus/targets/cadvisor-srv-app-01.yml << EOF
- targets: [192.168.1.101:8080]
  labels:
    instance: srv-app-01
    env: production
EOF
```

Prometheus recharge les targets automatiquement toutes les 60 secondes — pas besoin de redémarrer.

---

## 5. Intégrer une nouvelle application

Toute application qui envoie des données OpenTelemetry apparaît automatiquement dans Grafana.

### 5.1 Variable d'environnement à configurer

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://srv-observability:4317
OTEL_SERVICE_NAME=nom-de-mon-application
OTEL_RESOURCE_ATTRIBUTES=deployment.environment=production,service.version=1.0.0
```

> Remplacer `srv-observability` par l'IP ou le hostname du serveur observabilité.

### 5.2 Format de log recommandé

Les applications doivent émettre des logs JSON :

```json
{
  "timestamp": "2026-06-13T12:00:00Z",
  "level": "ERROR",
  "service": "payment-api",
  "message": "Database timeout",
  "trace_id": "abc123def456"
}
```

### 5.3 Exemples par langage

**Python**
```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

provider = TracerProvider()
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter())  # lit OTEL_EXPORTER_OTLP_ENDPOINT
)
trace.set_tracer_provider(provider)
```

**Node.js**
```javascript
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-grpc');

const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter(),  // lit OTEL_EXPORTER_OTLP_ENDPOINT
});
sdk.start();
```

**Java (Spring Boot)**
```yaml
# application.yml
management:
  otlp:
    metrics:
      export:
        url: ${OTEL_EXPORTER_OTLP_ENDPOINT}/v1/metrics
  tracing:
    sampling:
      probability: 1.0
```

**.NET**
```csharp
builder.Services.AddOpenTelemetry()
    .WithTracing(b => b
        .AddAspNetCoreInstrumentation()
        .AddOtlpExporter());  // lit OTEL_EXPORTER_OTLP_ENDPOINT
```

---

## 6. Alerting

### 6.1 Alertes configurées

| Alerte | Seuil | Sévérité | Notification |
|---|---|---|---|
| ApplicationDown | service inaccessible > 1 min | critical | Teams + Email |
| ContainerDown | container arrêté > 1 min | critical | Teams + Email |
| NodeDown | serveur inaccessible > 1 min | critical | Teams + Email |
| DiskCritical | disque > 95% | critical | Teams + Email |
| HighCPU | CPU > 80% pendant 5 min | warning | Teams |
| HighMemory | RAM > 80% pendant 5 min | warning | Teams |
| HighResponseTime | P95 > 2s pendant 5 min | warning | Teams |
| DiskWarning | disque > 80% | warning | Teams |
| HighErrorRate | 5xx > 5% pendant 5 min | warning | Teams |
| ContainerRestarted | redémarrage détecté | info | Teams |

### 6.2 Créer une alerte Grafana

1. Ouvrir n'importe quel dashboard
2. Éditer un panel → onglet **Alert**
3. Définir la condition et le seuil
4. Choisir le contact point : **Teams** ou **Email**

### 6.3 Tester les notifications

```bash
# Tester AlertManager directement
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {"alertname": "TestAlert", "severity": "warning"},
    "annotations": {"summary": "Test de notification"}
  }]'
```

---

## 7. Commandes utiles

### État de la stack

```bash
# Voir tous les services
docker compose ps

# Logs d'un service
docker compose logs -f grafana
docker compose logs -f otelcollector
docker compose logs -f prometheus

# Santé OTel Collector
curl http://localhost:13133/
```

### Recharger une configuration

```bash
# Recharger Prometheus (sans redémarrage)
curl -X POST http://localhost:9090/-/reload

# Recharger AlertManager
curl -X POST http://localhost:9093/-/reload

# Redémarrer un service
docker compose restart grafana
```

### Vérifier les métriques reçues

```bash
# Métriques exposées par OTel Collector
curl http://localhost:8889/metrics | grep otel_

# Targets Prometheus (UP/DOWN)
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job:.labels.job, instance:.labels.instance, health:.health}'
```

### Mise à jour de la stack

```bash
docker compose pull
docker compose up -d
```

---

## 8. Architecture des flux de données

```
Applications (Python, Java, NodeJS, Go, .NET)
        │
        │  OTLP gRPC :4317 / HTTP :4318
        ▼
┌─────────────────────────┐
│  OpenTelemetry Collector │
│  Reçoit : Metrics        │
│           Logs           │
│           Traces         │
└──────┬──────────┬────────┘
       │          │
  Metrics       Logs          Traces
       │          │               │
       ▼          ▼               ▼
 Prometheus      Loki           Tempo
 (scrape :8889)  (:3100)       (:4317)
       │          │               │
       └──────────┴───────────────┘
                  │
                  ▼
              Grafana
         Dashboards + Alerting
                  │
          ┌───────┴────────┐
          ▼                ▼
        Teams            Email
   (webhook)      (smtp.office365.com)

Serveurs
  Node Exporter ──→ Prometheus (métriques OS)
  cAdvisor      ──→ Prometheus (métriques Docker)
```

---

## 9. Dépannage

### Grafana ne charge pas les datasources

```bash
docker compose logs grafana | grep -i error
# Vérifier que prometheus/loki/tempo sont UP
docker compose ps
```

### OTel Collector refuse les connexions

```bash
# Vérifier les ports exposés
docker compose port otelcollector 4317
docker compose port otelcollector 4318

# Vérifier la config
docker compose logs otelcollector
```

### Loki ne reçoit pas les logs

```bash
# Tester l'endpoint Loki directement
curl -X POST http://localhost:3100/loki/api/v1/push \
  -H "Content-Type: application/json" \
  -d '{"streams":[{"stream":{"job":"test"},"values":[["'"$(date +%s%N)"'","test message"]]}]}'
```

### Prometheus ne scrape pas un target

```bash
# Vérifier l'état des targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health != "up")'
```

### Alertes ne partent pas sur Teams

1. Vérifier le webhook dans `alertmanager/alertmanager.yml`
2. Vérifier les logs AlertManager : `docker compose logs alertmanager`
3. Tester manuellement avec le curl de la section 6.3

---

## 10. Sauvegardes

Les données sont dans des volumes Docker. Pour sauvegarder :

```bash
# Lister les volumes
docker volume ls | grep observability

# Sauvegarder Grafana (dashboards personnalisés, users)
docker run --rm \
  -v observability_grafana_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/grafana-$(date +%Y%m%d).tar.gz /data

# Sauvegarder Prometheus
docker run --rm \
  -v observability_prometheus_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/prometheus-$(date +%Y%m%d).tar.gz /data
```
