from flask import Flask, jsonify
from dotenv import load_dotenv

from .config import Config
from .database import db
from .telemetry import setup_logging, setup_prometheus, setup_otel
from .routes import tasks_bp, health_bp, docs_bp

load_dotenv()


def create_app(overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    if overrides:
        app.config.update(overrides)

    setup_logging(app.config["LOG_LEVEL"])

    db.init_app(app)
    with app.app_context():
        db.create_all()

    setup_prometheus(app)
    setup_otel(app)

    app.register_blueprint(tasks_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(docs_bp)

    @app.errorhandler(404)
    def not_found(err):
        return jsonify({"error": str(err.description)}), 404

    @app.errorhandler(405)
    def method_not_allowed(err):
        return jsonify({"error": "Méthode non autorisée"}), 405

    @app.errorhandler(500)
    def internal_error(err):
        return jsonify({"error": "Erreur interne du serveur"}), 500

    return app
