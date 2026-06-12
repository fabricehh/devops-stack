# 🚦 Installation de Traefik v3 avec Let's Encrypt sur Ubuntu

> **Traefik** est un reverse proxy moderne qui s'intègre nativement avec Docker  
> et gère automatiquement les certificats SSL via **Let's Encrypt**.

---

## 🧠 1. Prérequis

Avant de commencer, assurez-vous d'avoir :

- Serveur **Ubuntu** (20.04 / 22.04 / 24.04)
- **Docker** installé ([voir guide d'installation](./installer-docker.md))
- **Docker Compose plugin** installé
- Un **nom de domaine** pointant vers votre serveur (ex: `devitlab.ddns.net`)
- Les **ports suivants ouverts** dans votre pare-feu :

| Port | Protocole | Usage |
|------|-----------|-------|
| `80` | HTTP | Challenge Let's Encrypt + redirection |
| `443` | HTTPS | Trafic sécurisé |

---

# 1. Créer le réseau partagé (une seule fois)
docker network create traefik-net


## 📁 2. Création du dossier Traefik

```bash
mkdir -p ~/traefik
cd ~/traefik
```
---

## 🔐 3. Fichier ACME (stockage des certificats Let's Encrypt)

```bash
touch acme.json
chmod 600 acme.json
```

> ⚠️ Le `chmod 600` est **obligatoire** — Traefik refuse de démarrer si les permissions sont trop ouvertes.

---

## 📄 4. Fichier `docker-compose.yml`

Créez le fichier de configuration :

```bash
nano docker-compose.yml
```

Collez le contenu suivant :

```yaml
services:
  traefik:
    image: traefik:v3.0
    container_name: traefik

    command:
      # Activation du dashboard
      - --api.dashboard=true

      # Intégration Docker
      - --providers.docker=true
      - --providers.docker.exposedbydefault=false

      # Points d'entrée réseau
      - --entrypoints.web.address=:80
      - --entrypoints.websecure.address=:443

      # Let's Encrypt — remplacez l'email par le vôtre
      - --certificatesresolvers.letsencrypt.acme.email=youremail@example.com
      - --certificatesresolvers.letsencrypt.acme.storage=/acme.json
      - --certificatesresolvers.letsencrypt.acme.httpchallenge=true
      - --certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web

    ports:
      - "80:80"
      - "443:443"

    labels:
      - traefik.enable=true
      # Route vers le dashboard Traefik
      - traefik.http.routers.dashboard.rule=Host(`traefik.devitlab.ddns.net`)
      - traefik.http.routers.dashboard.service=api@internal
      - traefik.http.routers.dashboard.entrypoints=websecure
      - traefik.http.routers.dashboard.tls.certresolver=letsencrypt

    networks:
      - traefik-net

    volumes:
      # Accès au socket Docker (lecture seule)
      - /var/run/docker.sock:/var/run/docker.sock:ro
      # Persistance des certificats SSL
      - ./acme.json:/acme.json

networks:
  traefik-net:
    external: true

```

---

## 🚀 5. Lancer Traefik

```bash
# Démarrer en arrière-plan
docker compose up -d

# Vérifier que le conteneur tourne
docker ps
```

Vous devriez voir `traefik` avec le statut **Up**.

---

## 🔍 6. Accès & Debug

### Dashboard Traefik

Accédez à l'interface web depuis votre navigateur :

```
https://traefik.devitlab.ddns.net
```

### Consulter les logs en temps réel

```bash
docker logs -f traefik
```

### Commandes de diagnostic utiles

```bash
# Redémarrer Traefik
docker compose restart traefik

# Arrêter Traefik
docker compose down

# Vérifier la configuration réseau
docker inspect traefik
```

---

## 🌐 7. Exposer un service derrière Traefik

Pour ajouter un service (ex: une app web) derrière Traefik, ajoutez ces labels dans son `docker-compose.yml` :

```yaml
labels:
  - traefik.enable=true
  - traefik.http.routers.monapp.rule=Host(`monapp.devitlab.ddns.net`)
  - traefik.http.routers.monapp.entrypoints=websecure
  - traefik.http.routers.monapp.tls.certresolver=letsencrypt
  - traefik.http.services.monapp.loadbalancer.server.port=3000
```

> Remplacez `monapp` et `3000` par le nom et le port de votre application.

---

## 📋 Récapitulatif de la structure des fichiers

```
~/traefik/
├── docker-compose.yml   # Configuration Traefik
└── acme.json            # Certificats Let's Encrypt (généré automatiquement)
```

---

## 🔗 Ressources

- [Documentation officielle Traefik](https://doc.traefik.io/traefik/)
- [Traefik v3 — Guide de migration](https://doc.traefik.io/traefik/migration/v2-to-v3/)
- [Let's Encrypt](https://letsencrypt.org/)