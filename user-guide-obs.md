# Guide Utilisateur — Plateforme Observabilité

> Ce guide explique comment **utiliser** la plateforme au quotidien.  
> Pas de configuration, pas de code — juste ce que vous voyez à l'écran.

---

## Avant de commencer — Générer des données

Les dashboards sont vides sans trafic. Lancez le générateur de charge pour voir quelque chose immédiatement.

**Ouvrir un terminal sur le serveur et lancer :**

```bash
cd devops-stack
python demo-app/load_test.py --duration 300 --rps 10
```

Cela envoie **10 requêtes par seconde pendant 5 minutes** sur la Task API.  
Laissez tourner en arrière-plan pendant que vous explorez les dashboards.

> **Sans Python installé**, utiliser Docker :
> ```bash
> docker run --rm --network observability_monitoring \
>   -e API_URL=http://task-api:5000 \
>   python:3.12-slim bash -c \
>   "pip install requests -q && python /app/load_test.py --duration 300 --rps 10" \
>   -v $(pwd)/demo-app/load_test.py:/app/load_test.py
> ```

---

## Grafana — Vos tableaux de bord

**Accès :** https://grafana.devitlab.ddns.net  
**Login :** `admin` / mot de passe défini dans `.env`

---

### Naviguer vers les dashboards

Une fois connecté :

1. Cliquer sur **Dashboards** dans le menu de gauche (icône grille)
2. Cliquer sur le dossier **Infrastructure**
3. Vous voyez les 5 dashboards

---

### Dashboard Infrastructure — Santé du serveur

**À quoi ça sert :** Surveiller que le serveur ne sature pas.

Ouvrir **Infrastructure → Infrastructure**

Ce que vous voyez :

| Panneau | Lecture |
|---|---|
| **CPU Usage** | Courbe par serveur. Rouge = > 95%, orange = > 80% |
| **RAM Usage** | Idem. Si proche de 100% → redémarrer des containers |
| **Disque Usage** | Monte lentement. Alerte à 80% puis 95% |
| **Réseau** | Trafic entrant (RX) et sortant (TX) en bytes/s |

**Ce qu'il faut surveiller :** Une courbe qui monte progressivement sans redescendre.

---

### Dashboard Docker — Vos containers

**À quoi ça sert :** Voir ce que chaque container consomme.

Ouvrir **Infrastructure → Docker**

Ce que vous voyez :

| Panneau | Lecture |
|---|---|
| **Containers actifs** | Nombre vert. Doit rester stable |
| **Containers arrêtés** | Doit être à 0. Si > 0 → un service est tombé |
| **CPU par container** | Qui consomme le plus ? `task-api`, `grafana`, etc. |
| **RAM par container** | Détecter les fuites mémoire (courbe qui monte sans fin) |

**Astuce :** Cliquer sur un nom dans la légende pour isoler un container.

---

### Dashboard Applications — Santé de la Task API

**À quoi ça sert :** Savoir si l'application répond bien aux utilisateurs.

Ouvrir **Infrastructure → Applications**

Ce que vous voyez :

| Panneau | Lecture |
|---|---|
| **Requêtes / seconde** | Le trafic actuel. Normal si correspond à ce que vous attendez |
| **Temps de réponse P50 / P95** | P50 = temps médian. P95 = les 5% les plus lents. Alerte si P95 > 2s |
| **Taux d'erreurs 5xx** | Doit être à 0%. Toute valeur > 0 = bug à investiguer |
| **Disponibilité 24h** | Doit être à 100%. En dessous de 99% = problème sérieux |

**Lecture rapide :** Tout vert = tout va bien. Orange/rouge = regarder les logs.

---

### Dashboard Logs — Chercher dans les logs

**À quoi ça sert :** Trouver ce qui s'est passé quand une erreur survient.

Ouvrir **Infrastructure → Logs**

#### Filtrer par niveau

En haut à gauche, variable **Niveau** : sélectionner `ERROR`, `WARNING` ou `INFO`.

Pour voir uniquement les erreurs : décocher tout sauf `ERROR`.

#### Faire une recherche

En haut, champ **Recherche** : taper un mot clé.

Exemples :
- `timeout` → trouver tous les timeouts
- `task_created` → voir toutes les créations de tâches
- `500` → voir les erreurs HTTP 500

#### Lire un log

Cliquer sur **>** à gauche d'une ligne pour voir tous les détails :

```
timestamp   : 2026-06-13T10:00:00Z
level       : ERROR
name        : app.routes.tasks
message     : task_created
task_id     : 42
trace_id    : abc123def456      ← cliquer pour voir la trace !
```

#### Aller de log à trace

Sur le champ `trace_id` → cliquer sur **Voir dans Tempo**.  
La trace complète de la requête s'ouvre.

---

### Dashboard Traces — Suivre une requête de bout en bout

**À quoi ça sert :** Comprendre exactement où une requête a perdu du temps.

Ouvrir **Infrastructure → Traces**

#### Lire les métriques de traces

| Panneau | Lecture |
|---|---|
| **Appels par service** | Trafic reçu par chaque microservice |
| **Latence P95** | Où les 5% les plus lentes perdent du temps |
| **Taux d'erreurs** | Spans qui se terminent en erreur |
| **Service Map** | Graphe des dépendances entre services |

#### Explorer une trace individuelle

1. Menu gauche → **Explore**
2. Sélectionner la datasource **Tempo**
3. Dans le champ **TraceQL** : taper `{}` et appuyer sur `Maj+Entrée`
4. Cliquer sur un `TraceID` dans les résultats

Vous voyez la cascade de la requête :

```
POST /api/v1/tasks         [42ms]  ← durée totale
  └── INSERT INTO tasks    [3ms]   ← appel base de données
```

**Identifier une lenteur :** la barre la plus longue = le goulet d'étranglement.

---

## Prometheus — Explorer les métriques brutes

**Accès :** https://prometheus.devitlab.ddns.net

Prometheus permet d'écrire des requêtes pour interroger n'importe quelle métrique.

### Vérifier que tout est surveillé

1. Menu en haut → **Status → Targets**
2. Tout doit être en **vert (UP)**

Si un service est en rouge : il est inaccessible ou arrêté.

### Requêtes utiles à tester

Aller dans **Graph** (menu du haut) et coller ces requêtes :

**CPU du serveur en % :**
```
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```

**RAM utilisée en % :**
```
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
```

**Nombre de requêtes par seconde sur la Task API :**
```
rate(flask_http_request_total[1m])
```

**Containers Docker actuellement actifs :**
```
count(container_last_seen{image!=""})
```

Cliquer sur l'onglet **Graph** pour voir l'évolution dans le temps.

---

## AlertManager — Gérer les alertes

**Accès :** https://alertmanager.devitlab.ddns.net

### Ce que vous voyez

- **Onglet Alerts :** toutes les alertes actuellement actives
- **Onglet Silences :** alertes mises en sourdine

### Silence une alerte pendant une maintenance

Si vous savez qu'un serveur va être en maintenance et que vous ne voulez pas recevoir d'alertes :

1. Onglet **Silences** → bouton **New Silence**
2. **Matcher :** `instance = srv-app-01`
3. **Duration :** durée de la maintenance (ex: 2h)
4. **Comment :** `Maintenance planifiée`
5. Cliquer **Create**

Les alertes de ce serveur ne partiront pas sur Teams/Email pendant cette période.

### Tester qu'une notification Teams fonctionne

```bash
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {"alertname": "TestManuel", "severity": "warning"},
    "annotations": {"summary": "Test depuis AlertManager"}
  }]'
```

Un message doit apparaître dans le canal Teams dans les 30 secondes.

---

## Scénarios du quotidien

### "Une application est lente — où regarder ?"

1. **Dashboard Applications** → colonne **Temps de réponse P95** : montée anormale ?
2. **Dashboard Traces** → panneau **Latence P95** : quel service est lent ?
3. **Explore → Tempo** : trouver une trace lente et identifier la barre la plus longue
4. **Dashboard Logs** : chercher `ERROR` dans les logs de la période concernée

---

### "Un utilisateur signale une erreur — retrouver ce qui s'est passé"

1. **Dashboard Logs** → champ **Recherche** : taper `ERROR`
2. Régler l'intervalle de temps en haut à droite sur la période signalée
3. Développer le log d'erreur → copier le `trace_id`
4. **Explore → Tempo** → coller le `trace_id` dans **TraceID**
5. La trace montre exactement quelle ligne de code a échoué et pourquoi

---

### "Le serveur semble lent ce matin — diagnostic rapide"

1. **Dashboard Infrastructure** → CPU et RAM : pic anormal ?
2. **Dashboard Docker** → quel container consomme trop ?
3. **Prometheus → Status → Targets** : tous les services sont-ils UP ?
4. Si un service est DOWN → `docker compose logs <service>` sur le serveur

---

### "Je veux voir l'impact d'un déploiement"

1. Noter l'heure du déploiement
2. **Dashboard Applications** : régler l'intervalle sur "avant / après déploiement"
3. Comparer **Temps de réponse** et **Taux d'erreurs** avant et après
4. Si dégradation → rollback et consulter les **Logs** pour trouver la cause

---

## Réglage de la période de temps

En haut à droite de chaque dashboard, le sélecteur de période :

| Valeur | Usage |
|---|---|
| **Last 15 minutes** | Incident en cours |
| **Last 1 hour** | Analyse récente |
| **Last 3 hours** | Défaut par défaut |
| **Last 24 hours** | Bilan journalier |
| **Last 7 days** | Tendances hebdomadaires |

Cliquer sur **🔄 (refresh)** à droite pour choisir le rafraîchissement automatique :  
`5s` pour suivre un incident en direct, `1m` pour la surveillance normale.
