from fastapi.testclient import TestClient
from helpers import register_user, login_user, auth_header


def test_register_user(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={"name": "alice", "password": "pass123", "role": "user"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "alice" in data["message"]
    assert "user" in data["message"]


def test_register_duplicate_username(client: TestClient) -> None:
    register_user(client, name="bob", password="pass123")
    response = client.post(
        "/auth/register",
        json={"name": "bob", "password": "other", "role": "user"},
    )
    assert response.status_code == 400
    assert "Username taken" in response.json()["detail"]


def test_register_admin(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={"name": "admin1", "password": "admin", "role": "admin"},
    )
    assert response.status_code == 200
    assert "admin" in response.json()["message"]


def test_register_second_admin_fails(client: TestClient) -> None:
    register_user(client, name="admin1", password="admin", role="admin")
    response = client.post(
        "/auth/register",
        json={"name": "admin2", "password": "admin2", "role": "admin"},
    )
    assert response.status_code == 422
    assert "admin user already exists" in response.json()["detail"].lower()


def test_login_success(client: TestClient) -> None:
    register_user(client, name="charlie", password="secret")
    response = client.post(
        "/auth/login",
        data={"username": "charlie", "password": "secret"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient) -> None:
    register_user(client, name="dave", password="correct")
    response = client.post(
        "/auth/login",
        data={"username": "dave", "password": "wrong"},
    )
    assert response.status_code == 400
    assert "Invalid credentials" in response.json()["detail"]


def test_login_nonexistent_user(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        data={"username": "nobody", "password": "pass"},
    )
    assert response.status_code == 400


def test_force_delete_user(client: TestClient) -> None:
    register_user(client, name="deleteme", password="pass")
    response = client.delete(
        "/force-delete-user", params={"name": "deleteme"}
    )
    assert response.status_code == 200
    assert "deleteme" in response.json()["message"]

    login_resp = client.post(
        "/auth/login",
        data={"username": "deleteme", "password": "pass"},
    )
    assert login_resp.status_code == 400


def test_protected_endpoint_without_token(client: TestClient) -> None:
    response = client.post(
        "/send-friend-request", params={"receiver_id": 1}
    )
    assert response.status_code == 401
