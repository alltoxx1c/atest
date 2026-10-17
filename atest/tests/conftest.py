import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from rps.logging_config import shutdown_logging
from rps.models import Base


@pytest.fixture
def session():
    """Чистая SQLite-база в памяти для каждого теста."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.fixture(autouse=True)
def _close_log_handlers():
    yield
    shutdown_logging()
