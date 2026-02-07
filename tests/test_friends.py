from fastapi.testclient import TestClient
from helpers import register_user, login_user, auth_header


def test_send_friend_request(client: TestClient) -> None:
    register_user(client, name="alice", password="pass")
    register_user(client, name="bob", password="pass")
    alice_token = login_user(client, name="alice", password="pass")

    response = client.post(
        "/send-friend-request",
        params={"receiver_id": 2},
        headers=auth_header(alice_token),
    )
    assert response.status_code == 200
    assert "sent successfully" in response.json()["message"]


def test_accept_friend_request(client: TestClient) -> None:
    register_user(client, name="alice", password="pass")
    register_user(client, name="bob", password="pass")
    alice_token = login_user(client, name="alice", password="pass")
    bob_token = login_user(client, name="bob", password="pass")

    client.post(
        "/send-friend-request",
        params={"receiver_id": 2},
        headers=auth_header(alice_token),
    )

    response = client.post(
        "/respond-friend-request",
        params={"sender_id": 1, "action": "accept"},
        headers=auth_header(bob_token),
    )
    assert response.status_code == 200
    assert "accepted" in response.json()["message"]


def test_decline_friend_request(client: TestClient) -> None:
    register_user(client, name="alice", password="pass")
    register_user(client, name="bob", password="pass")
    alice_token = login_user(client, name="alice", password="pass")
    bob_token = login_user(client, name="bob", password="pass")

    client.post(
        "/send-friend-request",
        params={"receiver_id": 2},
        headers=auth_header(alice_token),
    )

    response = client.post(
        "/respond-friend-request",
        params={"sender_id": 1, "action": "decline"},
        headers=auth_header(bob_token),
    )
    assert response.status_code == 200
    assert "declined" in response.json()["message"]


def test_accept_nonexistent_request(client: TestClient) -> None:
    register_user(client, name="alice", password="pass")
    alice_token = login_user(client, name="alice", password="pass")

    response = client.post(
        "/respond-friend-request",
        params={"sender_id": 999, "action": "accept"},
        headers=auth_header(alice_token),
    )
    assert response.status_code == 404


def test_get_my_friends(client: TestClient) -> None:
    register_user(client, name="alice", password="pass")
    register_user(client, name="bob", password="pass")
    alice_token = login_user(client, name="alice", password="pass")
    bob_token = login_user(client, name="bob", password="pass")

    client.post(
        "/send-friend-request",
        params={"receiver_id": 2},
        headers=auth_header(alice_token),
    )
    client.post(
        "/respond-friend-request",
        params={"sender_id": 1, "action": "accept"},
        headers=auth_header(bob_token),
    )

    response = client.get(
        "/get-my-friends/1",
        headers=auth_header(alice_token),
    )
    assert response.status_code == 200
    friends = response.json()["friends"]
    assert len(friends) >= 1
    names = [f["name"] for f in friends]
    assert "bob" in names


def test_get_friends_empty(client: TestClient) -> None:
    register_user(client, name="loner", password="pass")
    token = login_user(client, name="loner", password="pass")

    response = client.get(
        "/get-my-friends/1",
        headers=auth_header(token),
    )
    assert response.status_code == 200
    assert response.json()["friends"] == []


def test_remove_friend(client: TestClient) -> None:
    register_user(client, name="alice", password="pass")
    register_user(client, name="bob", password="pass")
    alice_token = login_user(client, name="alice", password="pass")
    bob_token = login_user(client, name="bob", password="pass")

    client.post(
        "/send-friend-request",
        params={"receiver_id": 2},
        headers=auth_header(alice_token),
    )
    client.post(
        "/respond-friend-request",
        params={"sender_id": 1, "action": "accept"},
        headers=auth_header(bob_token),
    )

    response = client.delete(
        "/remove-friend",
        params={"friend_id": 2},
        headers=auth_header(alice_token),
    )
    assert response.status_code == 200
    assert "removed" in response.json()["message"]


def test_remove_nonexistent_friend(client: TestClient) -> None:
    register_user(client, name="alice", password="pass")
    token = login_user(client, name="alice", password="pass")

    response = client.delete(
        "/remove-friend",
        params={"friend_id": 999},
        headers=auth_header(token),
    )
    assert response.status_code == 404


def test_duplicate_friend_request(client: TestClient) -> None:
    register_user(client, name="alice", password="pass")
    register_user(client, name="bob", password="pass")
    alice_token = login_user(client, name="alice", password="pass")

    client.post(
        "/send-friend-request",
        params={"receiver_id": 2},
        headers=auth_header(alice_token),
    )

    response = client.post(
        "/send-friend-request",
        params={"receiver_id": 2},
        headers=auth_header(alice_token),
    )
    assert response.status_code == 200
    assert "already" in response.json()["message"]
