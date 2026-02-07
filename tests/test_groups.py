from fastapi.testclient import TestClient
from helpers import register_user, login_user, auth_header


def _create_group(
    client: TestClient,
    token: str,
    name: str = "Test Group",
    owner_id: int = 1,
    member_ids: list[int] | None = None,
) -> object:

    return client.post(
        "/create-group",
        params={"name": name, "owner_id": owner_id},
        json=(member_ids or []),
        headers=auth_header(token),
    )


def test_create_group(client: TestClient) -> None:

    register_user(client, name="owner", password="pass")
    register_user(client, name="member1", password="pass")
    token = login_user(client, name="owner", password="pass")

    response = _create_group(
        client, token, name="Test Group",
        owner_id=1, member_ids=[2],
    )
    assert response.status_code == 200
    assert "created successfully" in response.json()["message"]


def test_create_group_no_members(client: TestClient) -> None:
    register_user(client, name="owner", password="pass")
    token = login_user(client, name="owner", password="pass")

    response = _create_group(
        client, token, name="Empty Group", owner_id=1, member_ids=[],
    )
    assert response.status_code == 200


def test_add_member_to_group(client: TestClient) -> None:
    register_user(client, name="owner", password="pass")
    register_user(client, name="new_member", password="pass")
    token = login_user(client, name="owner", password="pass")

    _create_group(client, token, name="MyGroup", owner_id=1)

    response = client.post(
        "/add-member",
        params={"group_id": 1, "new_member_id": 2},
        headers=auth_header(token),
    )
    assert response.status_code == 200
    assert "added" in response.json()["message"]


def test_add_duplicate_member(client: TestClient) -> None:
    register_user(client, name="owner", password="pass")
    register_user(client, name="member", password="pass")
    token = login_user(client, name="owner", password="pass")

    _create_group(
        client, token, name="G", owner_id=1, member_ids=[2],
    )

    response = client.post(
        "/add-member",
        params={"group_id": 1, "new_member_id": 2},
        headers=auth_header(token),
    )
    assert response.status_code == 400
    assert "already" in response.json()["detail"]


def test_add_member_nonexistent_group(client: TestClient) -> None:
    register_user(client, name="user1", password="pass")
    token = login_user(client, name="user1", password="pass")

    response = client.post(
        "/add-member",
        params={"group_id": 999, "new_member_id": 1},
        headers=auth_header(token),
    )
    assert response.status_code == 404


def test_add_member_not_owner(client: TestClient) -> None:
    register_user(client, name="owner", password="pass")
    register_user(client, name="non_owner", password="pass")
    register_user(client, name="target", password="pass")
    owner_token = login_user(client, name="owner", password="pass")
    other_token = login_user(
        client, name="non_owner", password="pass"
    )

    _create_group(client, owner_token, name="G", owner_id=1)

    response = client.post(
        "/add-member",
        params={"group_id": 1, "new_member_id": 3},
        headers=auth_header(other_token),
    )
    assert response.status_code == 403


def test_remove_group_member(client: TestClient) -> None:
    register_user(client, name="owner", password="pass")
    register_user(client, name="member", password="pass")
    token = login_user(client, name="owner", password="pass")

    _create_group(
        client, token, name="G", owner_id=1, member_ids=[2],
    )

    response = client.delete(
        "/remove-group-member",
        params={"group_id": 1, "user_id": 2},
        headers=auth_header(token),
    )
    assert response.status_code == 200
    assert "removed" in response.json()["message"]


def test_remove_member_not_owner(client: TestClient) -> None:
    register_user(client, name="owner", password="pass")
    register_user(client, name="member", password="pass")
    owner_token = login_user(client, name="owner", password="pass")
    member_token = login_user(client, name="member", password="pass")

    _create_group(
        client, owner_token, name="G", owner_id=1, member_ids=[2],
    )

    response = client.delete(
        "/remove-group-member",
        params={"group_id": 1, "user_id": 2},
        headers=auth_header(member_token),
    )
    assert response.status_code == 403


def test_delete_group(client: TestClient) -> None:
    register_user(client, name="owner", password="pass")
    token = login_user(client, name="owner", password="pass")

    _create_group(client, token, name="DeleteMe", owner_id=1)

    response = client.delete(
        "/delete-group",
        params={"group_id": 1},
        headers=auth_header(token),
    )
    assert response.status_code == 200
    assert "deleted" in response.json()["message"]


def test_delete_group_not_owner(client: TestClient) -> None:
    register_user(client, name="owner", password="pass")
    register_user(client, name="other", password="pass")
    owner_token = login_user(client, name="owner", password="pass")
    other_token = login_user(client, name="other", password="pass")

    _create_group(client, owner_token, name="G", owner_id=1)

    response = client.delete(
        "/delete-group",
        params={"group_id": 1},
        headers=auth_header(other_token),
    )
    assert response.status_code == 403


def test_delete_nonexistent_group(client: TestClient) -> None:
    register_user(client, name="user1", password="pass")
    token = login_user(client, name="user1", password="pass")

    response = client.delete(
        "/delete-group",
        params={"group_id": 999},
        headers=auth_header(token),
    )
    assert response.status_code == 404
