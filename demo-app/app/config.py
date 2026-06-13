import os


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///tasks.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "task-api")
    SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
    DEPLOYMENT_ENVIRONMENT = os.getenv("DEPLOYMENT_ENVIRONMENT", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
