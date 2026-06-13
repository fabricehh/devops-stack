# Observability Platform Standard

## Objectif

Mettre en place une plateforme unique permettant de superviser toutes les applications actuelles et futures.

La plateforme doit fournir :

* Monitoring
* Logs centralisés
* Distributed Tracing
* Alerting
* Notifications
* Tableaux de bord
* Gestion des incidents

Une nouvelle application doit simplement intégrer OpenTelemetry et être automatiquement visible dans Grafana.

---

# Architecture Globale

```text
                      +----------------+
                      |    Grafana     |
                      | Dashboards     |
                      | Alerting       |
                      +----------------+
                               ▲
                               │
      +------------------------+------------------------+
      │                        │                        │
      ▼                        ▼                        ▼

+-------------+      +----------------+      +-------------+
| Prometheus  |      |      Loki      |      |    Tempo    |
|  Metrics    |      |      Logs      |      |   Traces    |
+-------------+      +----------------+      +-------------+
       ▲                      ▲                     ▲
       └──────────────┬───────┴────────────┬────────┘
                      │                    │
                      ▼
           +--------------------------+
           | OpenTelemetry Collector  |
           +--------------------------+
                      ▲
                      │
        +-------------+--------------+
        │                            │

+---------------+          +----------------+
| Applications  |          | Applications   |
| Python        |          | NodeJS         |
| Java          |          | .NET           |
| Go            |          | NextJS         |
+---------------+          +----------------+

```

---

# Serveur Observabilité

Nom recommandé :

```text
srv-observability
```

Services installés :

```text
Traefik
Grafana
Prometheus
Loki
Tempo
OpenTelemetry Collector
AlertManager
```

---

# Serveurs Applicatifs

Chaque serveur applicatif contient :

```text
Docker
Node Exporter
cAdvisor
OpenTelemetry Agent
Applications
```

Exemple :

```text
srv-app-01
srv-app-02
srv-app-03
```

---

# Monitoring

## Prometheus

Collecte :

* CPU
* RAM
* Disque
* Réseau
* Temps de réponse
* Nombre de requêtes
* Nombre d'erreurs

Exemples :

```text
http_requests_total
http_request_duration_seconds
memory_usage
cpu_usage
```

---

# Monitoring Serveur

## Node Exporter

Collecte :

```text
CPU
RAM
Disk
Network
Load Average
```

---

# Monitoring Docker

## cAdvisor

Collecte :

```text
CPU Container
RAM Container
Network Container
Container State
```

---

# Logging

## Loki

Centralisation des logs.

Format recommandé :

```json
{
  "timestamp":"2026-06-13T12:00:00Z",
  "level":"ERROR",
  "service":"payment-api",
  "message":"Database timeout"
}
```

---

# Tracing

## Tempo

Suivi complet des requêtes.

Exemple :

```text
Client
 ↓
Traefik
 ↓
API
 ↓
Service
 ↓
Database
```

Permet d'identifier précisément les lenteurs.

---

# OpenTelemetry

## Standard Entreprise

Chaque application doit envoyer :

```text
Metrics
Logs
Traces
```

vers :

```text
OpenTelemetry Collector
```

---

# Dashboards Grafana

## Dashboard Infrastructure

Affiche :

```text
CPU
RAM
Disque
Réseau
Charge système
```

---

## Dashboard Docker

Affiche :

```text
Containers actifs
Containers arrêtés
CPU Docker
RAM Docker
```

---

## Dashboard Applications

Affiche :

```text
Temps de réponse
Nombre de requêtes
Nombre d'erreurs
Disponibilité
```

---

## Dashboard Logs

Affiche :

```text
ERROR
WARNING
INFO
```

avec moteur de recherche.

---

## Dashboard Traces

Affiche :

```text
Appels API
Temps d'exécution
Erreurs
```

---

# Alerting

## Critical

Déclenchement :

```text
Application DOWN
Database DOWN
Container DOWN
Disque > 95%
```

Action :

```text
Teams
Email
Ticket Incident
```

---

## Warning

Déclenchement :

```text
CPU > 80%
RAM > 80%
Response Time > 2s
```

Action :

```text
Teams
```

---

## Information

Déclenchement :

```text
Déploiement
Redémarrage
Maintenance
```

Action :

```text
Teams
```

---

# Notifications

## Microsoft Teams

Canal :

```text
DevOps Alerts
```

Connexion :

```text
Grafana Alerting
      ↓
Webhook Teams
```

---

## Email

Configuration SMTP :

```text
smtp.office365.com
Port 587
```

Utilisation :

```text
Incidents critiques
Rapports quotidiens
Rapports hebdomadaires
```

---

# Automatisation

## Power Automate

Flux :

```text
Grafana
   ↓
Power Automate
   ↓
Teams
Email
GLPI
Jira
SMS
```

---

# Gestion des Incidents

## Cas 1 : API DOWN

```text
API inaccessible
      ↓
Alerte Grafana
      ↓
Message Teams
      ↓
Email
      ↓
Création Ticket
```

---

## Cas 2 : CPU Elevé

```text
CPU > 80%
      ↓
Alerte Teams
```

---

## Cas 3 : Trop d'erreurs

```text
5xx > seuil
      ↓
Alerte Teams
      ↓
Ticket Incident
```

---

# Intégration d'une Nouvelle Application

## Étape 1

Installer OpenTelemetry SDK.

---

## Étape 2

Configurer :

```text
OTEL_EXPORTER_OTLP_ENDPOINT
```

---

## Étape 3

Déployer via GitLab CI/CD.

---

## Étape 4

L'application apparaît automatiquement dans :

```text
Grafana
Prometheus
Loki
Tempo
```

---

# CI/CD

Infrastructure existante :

```text
GitLab
GitLab Registry
GitLab Runner
Docker
Traefik
```

Pipeline :

```text
Git Push
   ↓
GitLab CI
   ↓
Build Docker
   ↓
Push Registry
   ↓
Deploy
   ↓
Observability Automatique
```

---

# Bénéfices

* Plateforme unique pour toutes les applications
* Réduction du temps de diagnostic
* Détection rapide des incidents
* Monitoring centralisé
* Logs centralisés
* Traces distribuées
* Alertes automatiques
* Notifications Teams et Email
* Compatible Docker, Kubernetes et VM
* Compatible Python, Java, NodeJS, Go et .NET
* Aucune modification de l'infrastructure lors de l'ajout d'une nouvelle application
