from fastapi.testclient import TestClient
from helpers import register_user, login_user, auth_header


def _make_friends(
    client: TestClient,
    token_a: str,
    token_b: str,
    id_a: int,
    id_b: int,
) -> None:
    client.post(
        "/send-friend-request",
        params={"receiver_id": id_b},
        headers=auth_header(token_a),
    )
    client.post(
        "/respond-friend-request",
        params={"sender_id": id_a, "action": "accept"},
        headers=auth_header(token_b),
    )


def test_send_message_to_friend(client: TestClient) -> None:
    register_user(client, name="alice", password="pass")
    register_user(client, name="bob", password="pass")
    alice_token = login_user(client, name="alice", password="pass")
    bob_token = login_user(client, name="bob", password="pass")

    _make_friends(client, alice_token, bob_token, 1, 2)

    response = client.post(
        "/send-message",
        params={"receiver_id": 2, "content": "Hi Bob!"},
        headers=auth_header(alice_token),
    )
    assert response.status_code == 200
    assert "sent" in response.json()["message"].lower()


def test_send_message_to_non_friend(client: TestClient) -> None:
    register_user(client, name="alice", password="pass")
    register_user(client, name="bob", password="pass")
    alice_token = login_user(client, name="alice", password="pass")

    response = client.post(
        "/send-message",
        params={"receiver_id": 2, "content": "Hi!"},
        headers=auth_header(alice_token),
    )
    assert response.status_code == 403


def test_send_message_to_nonexistent_user(
    client: TestClient,
) -> None:
    register_user(client, name="alice", password="pass")
    alice_token = login_user(client, name="alice", password="pass")

    response = client.post(
        "/send-message",
        params={"receiver_id": 999, "content": "Hello?"},
        headers=auth_header(alice_token),
    )
    assert response.status_code == 404


def test_get_chat_history(client: TestClient) -> None:
    register_user(client, name="alice", password="pass")
    register_user(client, name="bob", password="pass")
    alice_token = login_user(client, name="alice", password="pass")
    bob_token = login_user(client, name="bob", password="pass")

    _make_friends(client, alice_token, bob_token, 1, 2)

    client.post(
        "/send-message",
        params={"receiver_id": 2, "content": "Hey Bob!"},
        headers=auth_header(alice_token),
    )
    client.post(
        "/send-message",
        params={"receiver_id": 1, "content": "Hey Alice!"},
        headers=auth_header(bob_token),
    )

    response = client.get(
        "/get-chat",
        params={"other_user_id": 2},
        headers=auth_header(alice_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["messages"]) == 2
    assert data["messages"][0]["content"] == "Hey Bob!"
    assert data["messages"][1]["content"] == "Hey Alice!"


def test_get_empty_chat(client: TestClient) -> None:
    register_user(client, name="alice", password="pass")
    register_user(client, name="bob", password="pass")
    alice_token = login_user(client, name="alice", password="pass")

    response = client.get(
        "/get-chat",
        params={"other_user_id": 2},
        headers=auth_header(alice_token),
    )
    assert response.status_code == 200
    assert response.json()["messages"] == []


def test_chat_message_order(client: TestClient) -> None:
    register_user(client, name="alice", password="pass")
    register_user(client, name="bob", password="pass")
    alice_token = login_user(client, name="alice", password="pass")
    bob_token = login_user(client, name="bob", password="pass")

    _make_friends(client, alice_token, bob_token, 1, 2)

    for i in range(3):
        client.post(
            "/send-message",
            params={
                "receiver_id": 2,
                "content": f"Message {i}",
            },
            headers=auth_header(alice_token),
        )

    response = client.get(
        "/get-chat",
        params={"other_user_id": 2},
        headers=auth_header(alice_token),
    )
    messages = response.json()["messages"]
    assert len(messages) == 3
    assert messages[0]["content"] == "Message 0"
    assert messages[2]["content"] == "Message 2"
