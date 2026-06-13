import logging

from prometheus_flask_exporter import PrometheusMetrics
from pythonjsonlogger import jsonlogger

logger = logging.getLogger(__name__)


def setup_logging(log_level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(
        jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            rename_fields={"levelname": "level", "asctime": "timestamp"},
        )
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))


def setup_prometheus(app) -> PrometheusMetrics:
    metrics = PrometheusMetrics(
        app,
        default_labels={"service": app.config["SERVICE_NAME"]},
        group_by="endpoint",
    )
    metrics.info(
        "app_info",
        "Application info",
        version=app.config["SERVICE_VERSION"],
        environment=app.config["DEPLOYMENT_ENVIRONMENT"],
    )
    return metrics


def setup_otel(app) -> None:
    endpoint = app.config.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        logger.info("OTel désactivé — OTEL_EXPORTER_OTLP_ENDPOINT non configuré")
        return

    try:
        from opentelemetry import trace
        from opentelemetry import metrics as otel_metrics
        from opentelemetry._logs import set_logger_provider
        from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.flask import FlaskInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({
            "service.name": app.config["SERVICE_NAME"],
            "service.version": app.config["SERVICE_VERSION"],
            "deployment.environment": app.config["DEPLOYMENT_ENVIRONMENT"],
        })

        # Traces → Tempo via OTel Collector
        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True))
        )
        trace.set_tracer_provider(tracer_provider)

        # Métriques → Prometheus via OTel Collector
        reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=endpoint, insecure=True),
            export_interval_millis=15_000,
        )
        metrics_provider = MeterProvider(resource=resource, metric_readers=[reader])
        otel_metrics.set_meter_provider(metrics_provider)

        # Logs → Loki via OTel Collector
        log_provider = LoggerProvider(resource=resource)
        log_provider.add_log_record_processor(
            BatchLogRecordProcessor(OTLPLogExporter(endpoint=endpoint, insecure=True))
        )
        set_logger_provider(log_provider)
        logging.getLogger().addHandler(
            LoggingHandler(level=logging.NOTSET, logger_provider=log_provider)
        )

        # Auto-instrumentation Flask + SQLAlchemy
        FlaskInstrumentor().instrument_app(app)
        SQLAlchemyInstrumentor().instrument()

        logger.info("OpenTelemetry initialisé", extra={"endpoint": endpoint})

    except Exception as exc:
        logger.warning(f"Initialisation OTel échouée : {exc} — l'app continue sans traces")
