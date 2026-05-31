import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://astraeus:astraeus_dev@localhost/astraeus_test",
)

# Deferred imports to avoid triggering the real DB engine at import time
from app.models.base import Base
import app.models  # noqa: F401


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db(db_engine) -> Session:
    TestSession = sessionmaker(bind=db_engine, autocommit=False, autoflush=False)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        # Clear all rows between tests
        with db_engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE project_versions, project_media, projects, media, refresh_tokens, users RESTART IDENTITY CASCADE"))
            conn.commit()


@pytest.fixture()
def client(db) -> TestClient:
    from app.main import app
    from app.database import get_db

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
