# 🐳 Installation de Docker sur Ubuntu

> **Note :** Docker 28.x a atteint sa fin de support (EOL) en novembre 2025.  
> Il est recommandé d'utiliser la version **29.x** pour tout nouvel environnement.

---

## Prérequis

- Ubuntu 20.04 / 22.04 / 24.04 (64-bit)
- Accès `sudo`
- Connexion internet

---

## Étape 1 — Préparer le système

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
```

---

## Étape 2 — Ajouter la clé GPG officielle Docker

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

---

## Étape 3 — Ajouter le dépôt officiel Docker

```bash
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

---

## Étape 4 — Installer Docker

### Dernière version (recommandée)

```bash
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
```

### Version spécifique 28.1.1

```bash
sudo apt-get update
VERSION_STRING=5:28.1.1-1~ubuntu.$(lsb_release -rs)~$(lsb_release -cs)
sudo apt-get install -y \
  docker-ce=$VERSION_STRING \
  docker-ce-cli=$VERSION_STRING \
  containerd.io docker-buildx-plugin docker-compose-plugin
```

---

## Étape 5 — Vérifier l'installation

```bash
# Tester avec l'image hello-world
sudo docker run hello-world

# Vérifier la version installée
docker --version
```

---

## Étape 6 — Utiliser Docker sans `sudo` (optionnel)

```bash
sudo usermod -aG docker $USER
newgrp docker
```

> Déconnectez-vous puis reconnectez-vous pour que le changement prenne effet.

---

## Commandes utiles

| Commande | Description |
|---|---|
| `docker ps` | Lister les conteneurs actifs |
| `docker ps -a` | Lister tous les conteneurs |
| `docker images` | Lister les images locales |
| `docker pull <image>` | Télécharger une image |
| `docker run <image>` | Lancer un conteneur |
| `docker stop <id>` | Arrêter un conteneur |
| `docker rm <id>` | Supprimer un conteneur |
| `docker rmi <image>` | Supprimer une image |

---

## Désinstaller Docker

```bash
sudo apt-get purge docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
sudo rm -rf /var/lib/docker
sudo rm -rf /var/lib/containerd
```

---

## Ressources

- [Documentation officielle Docker](https://docs.docker.com/engine/install/ubuntu/)
- [Docker Hub](https://hub.docker.com/)
