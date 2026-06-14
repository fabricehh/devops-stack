# Guide Utilisateur — Observabilité PoC

> Stack légère : **Uptime Kuma** (monitoring) + **Dozzle** (logs)

---

## Démarrage

```bash
touch traefik/acme.json && chmod 600 traefik/acme.json
docker compose up -d
```

Vérifier :

```bash
docker compose ps
```

Résultat attendu :

```
NAME           STATUS
traefik        Up
uptime-kuma    Up
dozzle         Up
task-api       Up
```

---

## Uptime Kuma — Monitoring

**Accès :** https://uptime.devitlab.ddns.net

### Première connexion

1. Créer un compte administrateur (première visite uniquement)
2. Vous arrivez sur le tableau de bord

### Ajouter un monitor

1. Cliquer **Add New Monitor**
2. Remplir :

| Champ | Valeur |
|---|---|
| Monitor Type | `HTTP(s)` |
| Friendly Name | `Task API` |
| URL | `https://api.devitlab.ddns.net/health` |
| Heartbeat Interval | `60` secondes |

3. Cliquer **Save**

Le statut passe à 🟢 **Up** en quelques secondes.

### Ajouter une notification Teams

1. Menu en haut à droite → **Settings → Notifications**
2. **Add Notification**
3. Type : `Microsoft Teams`
4. Coller l'URL du webhook Teams
5. **Test** → un message apparaît dans Teams
6. **Save**
7. Revenir sur le monitor → **Edit** → cocher la notification → **Save**

### Ce que vous voyez sur le dashboard

| Indicateur | Signification |
|---|---|
| 🟢 Up | Service accessible |
| 🔴 Down | Service inaccessible — notification envoyée |
| Barre de temps | Historique de disponibilité (90 jours) |
| `24h Uptime` | % de disponibilité sur 24h |
| `Avg Response` | Temps de réponse moyen |

### Ajouter d'autres services à monitorer

Répéter l'étape "Ajouter un monitor" pour chaque URL à surveiller :

```
https://api.devitlab.ddns.net/health   → Task API
https://uptime.devitlab.ddns.net       → Uptime Kuma lui-même
https://logs.devitlab.ddns.net         → Dozzle
```

---

## Dozzle — Logs en temps réel

**Accès :** https://logs.devitlab.ddns.net

### Naviguer dans les logs

1. Liste des containers à gauche
2. Cliquer sur **task-api** pour voir ses logs en direct
3. Les logs défilent automatiquement

### Chercher dans les logs

- Champ **Search** en haut : taper un mot clé
- Exemple : `ERROR`, `task_created`, `500`

### Filtrer par niveau

Les logs JSON de la Task API affichent le champ `level` :
- `INFO` → opérations normales
- `WARNING` → attention requise
- `ERROR` → erreur à investiguer

### Astuce — Suivre un incident

1. Uptime Kuma détecte une panne → notification Teams
2. Ouvrir Dozzle → cliquer sur **task-api**
3. Chercher `ERROR` pour trouver la cause

---

## Générer du trafic (test)

```bash
python3 demo-app/load_test.py --duration 120 --rps 2
```

Dans Dozzle, les logs de **task-api** apparaissent en temps réel.  
Dans Uptime Kuma, le temps de réponse est visible sur le monitor.

---

## URLs

| Service | URL |
|---|---|
| Uptime Kuma | https://uptime.devitlab.ddns.net |
| Dozzle | https://logs.devitlab.ddns.net |
| Task API | https://api.devitlab.ddns.net |
| Swagger | https://api.devitlab.ddns.net/apidocs |
