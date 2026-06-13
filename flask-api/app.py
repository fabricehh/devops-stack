import logging
from flask import Flask
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

hello_counter = metrics.counter(
    "hello_requests_total", "Nombre de requêtes sur /",
    labels={"status": lambda r: r.status_code}
)


class HelloWorld(Resource):
    @hello_counter
    def get(self):
        """Retourne un message de bienvenue.
        ---
        responses:
          200:
            description: Message de bienvenue
            schema:
              properties:
                hello:
                  type: string
                  example: world
        """
        logger.info("Requête reçue sur /", extra={"endpoint": "/", "method": "GET"})
        return {"hello": "world"}


api.add_resource(HelloWorld, "/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
