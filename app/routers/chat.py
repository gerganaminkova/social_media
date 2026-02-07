import sqlite3
from fastapi import APIRouter, HTTPException, Depends
from database import get_db_connection
from utils import get_current_user

router = APIRouter()


@router.post("/send-message")
def send_message(
    receiver_id: int, content: str, current_user: dict = Depends(get_current_user)
):
    sender_id = current_user["id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
       SELECT id FROM users WHERE id = ?
    """,
        (receiver_id,),
    )
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="receiver not found")

    cursor.execute(
        """
        SELECT 1 FROM friends 
        WHERE ((user_id = ? AND friend_id = ?) 
           OR (user_id = ? AND friend_id = ?))
          AND status = 'accepted'
    """,
        (sender_id, receiver_id, receiver_id, sender_id),
    )

    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=403, detail="You can only message a friend!")

    cursor.execute(
        """
        INSERT INTO messages(sender_id, receiver_id, content) VALUES (?, ?, ?)
    """,
        (sender_id, receiver_id, content),
    )

    conn.commit()
    conn.close()

    return {"message": "Message sent successfully"}


@router.get("/get-chat")
def get_chat(other_user_id: int, current_user: dict = Depends(get_current_user)):
    user1_id = current_user["id"]
    user2_id = other_user_id

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT m.content, m.timestamp, u.name as sender_name
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE (m.sender_id = ? AND m.receiver_id = ?)
           OR (m.sender_id = ? AND m.receiver_id = ?)
        ORDER BY m.timestamp ASC
    """,
        (user1_id, user2_id, user2_id, user1_id),
    )

    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {
        "chat_participants": [
            user1_id,
            user2_id,
        ],
        "messages": messages,
    }
