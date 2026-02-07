from fastapi.testclient import TestClient


def register_user(
    client: TestClient,
    name: str = "testuser",
    password: str = "testpass",
    role: str = "user",
) -> dict:
    response = client.post(
        "/auth/register",
        json={"name": name, "password": password, "role": role},
    )
    return response.json()


def login_user(
    client: TestClient,
    name: str = "testuser",
    password: str = "testpass",
) -> str:
    response = client.post(
        "/auth/login",
        data={"username": name, "password": password},
    )
    return response.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
