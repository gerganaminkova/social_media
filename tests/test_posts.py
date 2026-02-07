from fastapi.testclient import TestClient
from helpers import register_user, login_user, auth_header


def test_create_text_post(client: TestClient) -> None:
    register_user(client, name="poster", password="pass")
    token = login_user(client, name="poster", password="pass")

    response = client.post(
        "/create-post",
        params={
            "post_type": "text",
            "content": "Hello world!",
            "visibility": "public",
        },
        headers=auth_header(token),
    )
    assert response.status_code == 200
    assert "posted successfully" in response.json()["message"]


def test_create_post_with_tags(client: TestClient) -> None:
    register_user(client, name="tagger", password="pass")
    token = login_user(client, name="tagger", password="pass")

    response = client.post(
        "/create-post",
        params={
            "post_type": "text",
            "content": "Tagged post",
            "visibility": "public",
            "tags": ["python", "fastapi"],
        },
        headers=auth_header(token),
    )
    assert response.status_code == 200


def test_create_group_post_without_group_id(
    client: TestClient,
) -> None:
    register_user(client, name="user1", password="pass")
    token = login_user(client, name="user1", password="pass")

    response = client.post(
        "/create-post",
        params={
            "post_type": "text",
            "content": "Group post",
            "visibility": "group",
        },
        headers=auth_header(token),
    )
    assert response.status_code == 422


def test_get_public_post(client: TestClient) -> None:
    register_user(client, name="author", password="pass")
    token = login_user(client, name="author", password="pass")

    client.post(
        "/create-post",
        params={
            "post_type": "text",
            "content": "Public post",
            "visibility": "public",
        },
        headers=auth_header(token),
    )

    response = client.get("/get-post/1")
    assert response.status_code == 200
    data = response.json()
    assert data["post_data"]["content"] == "Public post"


def test_get_post_with_tags(client: TestClient) -> None:
    register_user(client, name="author2", password="pass")
    token = login_user(client, name="author2", password="pass")

    client.post(
        "/create-post",
        params={
            "post_type": "text",
            "content": "Tagged",
            "visibility": "public",
            "tags": ["tech"],
        },
        headers=auth_header(token),
    )

    response = client.get("/get-post/1")
    assert response.status_code == 200
    assert "tech" in response.json()["tags"]


def test_delete_own_post(client: TestClient) -> None:
    register_user(client, name="deleter", password="pass")
    token = login_user(client, name="deleter", password="pass")

    client.post(
        "/create-post",
        params={
            "post_type": "text",
            "content": "To delete",
            "visibility": "public",
        },
        headers=auth_header(token),
    )

    response = client.delete(
        "/delete-post",
        params={"post_id": 1},
        headers=auth_header(token),
    )
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]


def test_delete_others_post_forbidden(client: TestClient) -> None:
    register_user(client, name="owner", password="pass")
    register_user(client, name="other", password="pass")
    owner_token = login_user(client, name="owner", password="pass")
    other_token = login_user(client, name="other", password="pass")

    client.post(
        "/create-post",
        params={
            "post_type": "text",
            "content": "Owner post",
            "visibility": "public",
        },
        headers=auth_header(owner_token),
    )

    response = client.delete(
        "/delete-post",
        params={"post_id": 1},
        headers=auth_header(other_token),
    )
    assert response.status_code == 403


def test_delete_nonexistent_post(client: TestClient) -> None:
    register_user(client, name="user99", password="pass")
    token = login_user(client, name="user99", password="pass")

    response = client.delete(
        "/delete-post",
        params={"post_id": 9999},
        headers=auth_header(token),
    )
    assert response.status_code == 404


def test_update_post(client: TestClient) -> None:
    register_user(client, name="editor", password="pass")
    token = login_user(client, name="editor", password="pass")

    client.post(
        "/create-post",
        params={
            "post_type": "text",
            "content": "Original",
            "visibility": "public",
        },
        headers=auth_header(token),
    )

    response = client.put(
        "/update-post/1",
        params={"content": "Updated"},
        headers=auth_header(token),
    )
    assert response.status_code == 200
    assert "updated successfully" in response.json()["message"]


def test_update_others_post_forbidden(client: TestClient) -> None:
    register_user(client, name="p_owner", password="pass")
    register_user(client, name="p_other", password="pass")
    owner_token = login_user(client, name="p_owner", password="pass")
    other_token = login_user(client, name="p_other", password="pass")

    client.post(
        "/create-post",
        params={
            "post_type": "text",
            "content": "Mine",
            "visibility": "public",
        },
        headers=auth_header(owner_token),
    )

    response = client.put(
        "/update-post/1",
        params={"content": "Hacked"},
        headers=auth_header(other_token),
    )
    assert response.status_code == 403


def test_get_nonexistent_post(client: TestClient) -> None:
    response = client.get("/get-post/9999")
    assert response.status_code == 404


def test_friends_only_post_blocked_for_non_friend(
    client: TestClient,
) -> None:
    register_user(client, name="private_user", password="pass")
    register_user(client, name="stranger", password="pass")
    private_token = login_user(
        client, name="private_user", password="pass"
    )
    stranger_token = login_user(
        client, name="stranger", password="pass"
    )

    client.post(
        "/create-post",
        params={
            "post_type": "text",
            "content": "Friends only",
            "visibility": "friends",
        },
        headers=auth_header(private_token),
    )

    response = client.get(
        "/get-post/1",
        headers=auth_header(stranger_token),
    )
    assert response.status_code == 403
