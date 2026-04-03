import pytest
from peewee import SqliteDatabase

from app.database import db as proxy_db
from app.models import Event, Url, User

test_db = SqliteDatabase(":memory:")
MODELS = [User, Url, Event]


@pytest.fixture(autouse=True)
def setup_db():
    proxy_db.initialize(test_db)
    test_db.connect(reuse_if_open=True)
    test_db.create_tables(MODELS)
    yield
    test_db.drop_tables(MODELS)
    if not test_db.is_closed():
        test_db.close()


@pytest.fixture()
def client(setup_db):
    from app import create_app
    from app.database import init_db

    app = create_app()
    app.config["TESTING"] = True
    # Re-init with test db so before_request uses SQLite
    init_db(app, database=test_db)

    with app.test_client() as c:
        yield c


@pytest.fixture()
def sample_user():
    return User.create(
        id=1,
        username="testuser",
        email="test@example.com",
        created_at="2025-01-01 00:00:00",
    )


@pytest.fixture()
def sample_url(sample_user):
    return Url.create(
        id=1,
        user=sample_user,
        short_code="abc123",
        original_url="https://example.com",
        title="Test",
        is_active=True,
        created_at="2025-01-01 00:00:00",
        updated_at="2025-01-01 00:00:00",
    )
