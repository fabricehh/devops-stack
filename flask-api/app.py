import logging
import time
from flask import Flask, request
from flask_restful import Resource, Api
from prometheus_flask_exporter import PrometheusMetrics
from pythonjsonlogger import jsonlogger

# ──────────────────────────────────────────
# LOGS JSON (pour Filebeat → Logstash → ES)
# ──────────────────────────────────────────
logger = logging.getLogger("flask-api")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s"
))
logger.addHandler(handler)

app = Flask(__name__)
api = Api(app)

# ──────────────────────────────────────────
# MÉTRIQUES PROMETHEUS (expose /metrics)
# ──────────────────────────────────────────
metrics = PrometheusMetrics(app)
metrics.info("app_info", "Informations API Flask", version="1.0.0")

# Compteur personnalisé
hello_counter = metrics.counter(
    "hello_requests_total", "Nombre de requêtes sur /",
    labels={"status": lambda r: r.status_code}
)


class HelloWorld(Resource):
    @hello_counter
    def get(self):
        logger.info("Requête reçue sur /", extra={
            "endpoint": "/",
            "method": "GET",
            "remote_addr": request.remote_addr,
        })
        return {"hello": "world"}


api.add_resource(HelloWorld, "/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
