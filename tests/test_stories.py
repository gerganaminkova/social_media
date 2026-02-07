from fastapi.testclient import TestClient
from helpers import register_user, login_user, auth_header


def test_create_public_story(client: TestClient) -> None:
    register_user(client, name="storyteller", password="pass")
    token = login_user(client, name="storyteller", password="pass")

    response = client.post(
        "/create-story",
        params={
            "content": "My first story!",
            "visibility": "public",
        },
        headers=auth_header(token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Story uploaded successfully"
    assert data["visibility"] == "public"
    assert "story_id" in data


def test_create_group_story_without_group_id(
    client: TestClient,
) -> None:
    register_user(client, name="user1", password="pass")
    token = login_user(client, name="user1", password="pass")

    response = client.post(
        "/create-story",
        params={"content": "Group story", "visibility": "group"},
        headers=auth_header(token),
    )
    assert response.status_code == 422


def test_react_to_story(client: TestClient) -> None:
    register_user(client, name="storyteller", password="pass")
    register_user(client, name="reactor", password="pass")
    st_token = login_user(
        client, name="storyteller", password="pass"
    )
    re_token = login_user(client, name="reactor", password="pass")

    client.post(
        "/create-story",
        params={
            "content": "Cool story",
            "visibility": "public",
        },
        headers=auth_header(st_token),
    )

    response = client.post(
        "/react-to-story",
        params={"story_id": 1, "emoji": "🔥"},
        headers=auth_header(re_token),
    )
    assert response.status_code == 200
    assert "🔥" in response.json()["message"]


def test_react_to_nonexistent_story(client: TestClient) -> None:
    register_user(client, name="reactor", password="pass")
    token = login_user(client, name="reactor", password="pass")

    response = client.post(
        "/react-to-story",
        params={"story_id": 999, "emoji": "😂"},
        headers=auth_header(token),
    )
    assert response.status_code == 404


def test_delete_own_story(client: TestClient) -> None:
    register_user(client, name="storyteller", password="pass")
    token = login_user(client, name="storyteller", password="pass")

    client.post(
        "/create-story",
        params={
            "content": "Delete me",
            "visibility": "public",
        },
        headers=auth_header(token),
    )

    response = client.delete(
        "/delete-story",
        params={"story_id": 1},
        headers=auth_header(token),
    )
    assert response.status_code == 200
    assert "deleted" in response.json()["message"]


def test_delete_others_story_forbidden(client: TestClient) -> None:
    register_user(client, name="owner", password="pass")
    register_user(client, name="other", password="pass")
    owner_token = login_user(client, name="owner", password="pass")
    other_token = login_user(client, name="other", password="pass")

    client.post(
        "/create-story",
        params={
            "content": "Not yours",
            "visibility": "public",
        },
        headers=auth_header(owner_token),
    )

    response = client.delete(
        "/delete-story",
        params={"story_id": 1},
        headers=auth_header(other_token),
    )
    assert response.status_code == 403


def test_delete_nonexistent_story(client: TestClient) -> None:
    register_user(client, name="user1", password="pass")
    token = login_user(client, name="user1", password="pass")

    response = client.delete(
        "/delete-story",
        params={"story_id": 999},
        headers=auth_header(token),
    )
    assert response.status_code == 404


def test_admin_can_delete_any_story(client: TestClient) -> None:
    register_user(client, name="admin1", password="pass", role="admin")
    register_user(client, name="user1", password="pass")
    admin_token = login_user(client, name="admin1", password="pass")
    user_token = login_user(client, name="user1", password="pass")

    client.post(
        "/create-story",
        params={
            "content": "User story",
            "visibility": "public",
        },
        headers=auth_header(user_token),
    )

    response = client.delete(
        "/delete-story",
        params={"story_id": 1},
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200


def test_get_stories(client: TestClient) -> None:
    register_user(client, name="storyteller", password="pass")
    token = login_user(client, name="storyteller", password="pass")

    client.post(
        "/create-story",
        params={
            "content": "Story 1",
            "visibility": "public",
        },
        headers=auth_header(token),
    )
    client.post(
        "/create-story",
        params={
            "content": "Story 2",
            "visibility": "public",
        },
        headers=auth_header(token),
    )

    response = client.get(
        "/get-stories",
        headers=auth_header(token),
    )
    assert response.status_code == 200
    stories = response.json()["stories"]
    assert len(stories) >= 2


def test_get_stories_unauthenticated(client: TestClient) -> None:
    register_user(client, name="storyteller", password="pass")
    token = login_user(client, name="storyteller", password="pass")

    client.post(
        "/create-story",
        params={
            "content": "Public story",
            "visibility": "public",
        },
        headers=auth_header(token),
    )

    response = client.get("/get-stories")
    assert response.status_code == 200


def test_story_reactions_in_listing(client: TestClient) -> None:
    register_user(client, name="storyteller", password="pass")
    register_user(client, name="reactor", password="pass")
    st_token = login_user(
        client, name="storyteller", password="pass"
    )
    re_token = login_user(client, name="reactor", password="pass")

    client.post(
        "/create-story",
        params={
            "content": "React to me!",
            "visibility": "public",
        },
        headers=auth_header(st_token),
    )

    client.post(
        "/react-to-story",
        params={"story_id": 1, "emoji": "❤️"},
        headers=auth_header(re_token),
    )

    response = client.get(
        "/get-stories",
        headers=auth_header(st_token),
    )
    stories = response.json()["stories"]
    assert len(stories) >= 1
    assert "reactions" in stories[0]
