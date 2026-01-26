import sqlite3
from fastapi import APIRouter, HTTPException
from database import get_db_connection
from models import FriendRequestAction


router = APIRouter()


@router.post("/send-friend-request")
def send_friend_request(sender_id: int, receiver_id: int):
    conn = get_db_connection() 
    cursor = conn.cursor()

    try:
        cursor.execute("""
        INSERT INTO friends (user_id, friend_id, status)
        VALUES (?,?, 'pending')
    """,(sender_id, receiver_id))
        conn.commit()
        msg = "Request sent successfully"
    except sqlite3.IntegrityError:
        msg = "Friend request already sent or you are already friends"

    conn.close()
    return{"message": msg}



@router.post("/respond-friend-request")
def respond_friend_request(user_id: int, sender_id: int, action: FriendRequestAction):
    conn = get_db_connection() 
    cursor = conn.cursor()

    if action == FriendRequestAction.ACCEPT:
        cursor.execute("""
            UPDATE friends 
            SET status = 'accepted' 
            WHERE user_id = ? AND friend_id = ? AND status = 'pending'
        """, (sender_id, user_id))
        
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="No pending request found to accept")
            
        msg = "Friend request accepted"

    elif action == FriendRequestAction.DECLINE:
        cursor.execute("""
            DELETE FROM friends 
            WHERE user_id = ? AND friend_id = ? AND status = 'pending'
        """, (sender_id, user_id))
        
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="No pending request found to decline")
            
        msg = "Friend request declined"

    conn.commit()
    conn.close()
    return {"message": msg}



@router.get("/get-my-friends/{user_id}")
def get_my_friends(user_id: int):
    conn = get_db_connection() 
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.id, u.name 
        FROM users u
        JOIN friends f ON (u.id = f.friend_id OR u.id = f.user_id)
        WHERE (f.user_id = ? OR f.friend_id = ?) 
          AND f.status = 'accepted'
          AND u.id != ?
    """, (user_id, user_id, user_id))
    
    friends = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"friends": friends}



@router.delete("/remove-friend")
def remove_friend(my_id: int, friend_id: int):
    conn = get_db_connection() 
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM friends 
        WHERE (user_id = ? AND friend_id = ?) 
           OR (user_id = ? AND friend_id = ?)
    """, (my_id, friend_id, friend_id, my_id))

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Friendship not found")

    conn.commit()
    conn.close()
    return {"message": "Friend removed successfully"}

