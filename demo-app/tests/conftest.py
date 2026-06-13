import pytest
from app import create_app
from app.database import db as _db
from app.models import Task


@pytest.fixture(scope="session")
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "OTEL_EXPORTER_OTLP_ENDPOINT": "",   # OTel désactivé en test
    })
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_db(app):
    yield
    with app.app_context():
        _db.session.query(Task).delete()
        _db.session.commit()


@pytest.fixture
def task(app):
    with app.app_context():
        t = Task(title="Test task", priority="high", status="pending")
        _db.session.add(t)
        _db.session.commit()
        return {"id": t.id, "title": t.title, "status": t.status, "priority": t.priority}
