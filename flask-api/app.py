import logging
from flask import Flask, request
from flask_restful import Resource, Api
from flasgger import Swagger
from prometheus_flask_exporter import PrometheusMetrics
from pythonjsonlogger import jsonlogger

logger = logging.getLogger("flask-api")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s"
))
logger.addHandler(handler)



app = Flask(__name__)
api = Api(app)
swagger_config = Swagger.DEFAULT_CONFIG.copy()
swagger_config["specs_route"] = "/swagger/"
swagger = Swagger(app, config=swagger_config)

metrics = PrometheusMetrics(app)
metrics.info("app_info", "Informations API Flask", version="1.0.0")

# Stockage en mémoire
items = {}
next_id = 1


class ItemList(Resource):
    def get(self):
        """Liste tous les items.
        ---
        responses:
          200:
            description: Liste des items
        """
        logger.info("GET /items", extra={"endpoint": "/items"})
        return {"items": list(items.values())}, 200

    def post(self):
        """Crée un item.
        ---
        parameters:
          - in: body
            name: body
            required: true
            schema:
              properties:
                name:
                  type: string
                  example: "mon item"
        responses:
          201:
            description: Item créé
          400:
            description: Champ name manquant
        """
        global next_id
        data = request.get_json(silent=True)
        if not data or "name" not in data:
            logger.warning("POST /items — body invalide")
            return {"error": "Le champ 'name' est requis"}, 400

        item = {"id": next_id, "name": data["name"]}
        items[next_id] = item
        next_id += 1
        logger.info("POST /items — item créé", extra={"item": item})
        return item, 201


class Item(Resource):
    def get(self, item_id):
        """Récupère un item par ID.
        ---
        parameters:
          - in: path
            name: item_id
            type: integer
            required: true
        responses:
          200:
            description: Item trouvé
          404:
            description: Item introuvable
        """
        item = items.get(item_id)
        if not item:
            logger.warning("GET /items/<id> — introuvable", extra={"item_id": item_id})
            return {"error": f"Item {item_id} introuvable"}, 404
        logger.info("GET /items/<id>", extra={"item_id": item_id})
        return item, 200

    def put(self, item_id):
        """Met à jour un item.
        ---
        parameters:
          - in: path
            name: item_id
            type: integer
            required: true
          - in: body
            name: body
            required: true
            schema:
              properties:
                name:
                  type: string
        responses:
          200:
            description: Item mis à jour
          400:
            description: Body invalide
          404:
            description: Item introuvable
        """
        if item_id not in items:
            return {"error": f"Item {item_id} introuvable"}, 404
        data = request.get_json(silent=True)
        if not data or "name" not in data:
            return {"error": "Le champ 'name' est requis"}, 400
        items[item_id]["name"] = data["name"]
        logger.info("PUT /items/<id>", extra={"item_id": item_id})
        return items[item_id], 200

    def delete(self, item_id):
        """Supprime un item.
        ---
        parameters:
          - in: path
            name: item_id
            type: integer
            required: true
        responses:
          200:
            description: Item supprimé
          404:
            description: Item introuvable
        """
        if item_id not in items:
            return {"error": f"Item {item_id} introuvable"}, 404
        deleted = items.pop(item_id)
        logger.info("DELETE /items/<id>", extra={"item_id": item_id})
        return {"deleted": deleted}, 200


class SimulateError(Resource):
    def get(self):
        """Simule une erreur 500.
        ---
        responses:
          500:
            description: Erreur serveur simulée
        """
        logger.error("Erreur 500 simulée", extra={"endpoint": "/error"})
        return {"error": "Erreur interne simulée"}, 500


api.add_resource(ItemList,     "/items")
api.add_resource(Item,         "/items/<int:item_id>")
api.add_resource(SimulateError, "/error")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
