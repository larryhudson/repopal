import hashlib
import hmac
import json
from typing import Any, Dict, Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from repopal.core.database import Base, get_db
from repopal.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]


def pytest_configure(config):
    """Register the 'integration' marker"""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test that uses real external services",
    )

@pytest.fixture
def test_repo(tmp_path):
    """Create a test git repository"""
    from git import Repo

    repo_dir = tmp_path / "test-repo"
    repo_dir.mkdir()

    # Initialize git repo
    repo = Repo.init(repo_dir)

    # Create a test file
    test_file = repo_dir / "test.txt"
    test_file.write_text("Hello world! This is a test file.")

    # Commit the file
    repo.index.add(["test.txt"])
    repo.index.commit("Initial commit")

    return repo_dir

@pytest.fixture
def webhook_signature():
    """Fixture to generate webhook signatures for testing"""
    def _generate_signature(webhook_secret: str, payload: Dict[str, Any]) -> Tuple[Dict[str, str], bytes]:
        payload_bytes = json.dumps(payload).encode()
        signature = hmac.new(
            key=webhook_secret.encode(),
            msg=payload_bytes,
            digestmod=hashlib.sha256
        ).hexdigest()

        headers = {
            "X-Hub-Signature-256": f"sha256={signature}"
        }

        return headers, payload_bytes

    return _generate_signature
