from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_create_user(client: TestClient, db: Session):
    response = client.post(
        "/api/users/", json={"email": "test@example.com", "name": "Test User"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert "id" in data
