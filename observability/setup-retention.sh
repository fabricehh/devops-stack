#!/usr/bin/env bash
# Configuration de la rétention des logs Elasticsearch (7 jours)
# À exécuter UNE FOIS après le premier démarrage de la stack.

set -e

ES_URL="${ES_URL:-http://localhost:9200}"

echo "→ Attente de la disponibilité d'Elasticsearch..."
until curl -s "$ES_URL/_cluster/health" > /dev/null; do
  sleep 2
done
echo "✓ Elasticsearch est prêt"

echo "→ Création de la politique ILM (suppression après 7 jours)..."
curl -s -X PUT "$ES_URL/_ilm/policy/logs-retention" \
  -H 'Content-Type: application/json' -d '{
  "policy": {
    "phases": {
      "delete": {
        "min_age": "7d",
        "actions": { "delete": {} }
      }
    }
  }
}'
echo ""

echo "→ Application de la politique aux index filebeat-*..."
curl -s -X PUT "$ES_URL/_index_template/filebeat-template" \
  -H 'Content-Type: application/json' -d '{
  "index_patterns": ["filebeat-*"],
  "template": {
    "settings": {
      "index.lifecycle.name": "logs-retention",
      "number_of_replicas": 0
    }
  }
}'
echo ""

echo "✓ Rétention configurée : les logs de plus de 7 jours seront supprimés automatiquement."
