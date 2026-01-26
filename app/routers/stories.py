import sqlite3
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from database import get_db_connection
from models import Visibility, Role

router = APIRouter()

@router.post("/create-story")
def create_story(
    uploader_id: int,
    content: str,
    visibility: Visibility,
    group_id: Optional[int] = None
):
    conn = get_db_connection

    cursor = conn.cursor

    cursor.execute("""
        SELECT role FROM user WHERE is = ?
    """, (uploader_id))
    user_row = cursor.fetchone()

    if not user_row:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
    
    user_lore = dict(user_row)["role"]

    if user_row == Role.GUEST.value:
        conn.close()
        raise HTTPException(status_code=403, detail="Guests cannot upload stories")
    
    if visibility == Visibility.GROUP and group_id is None:
        conn.close()
        raise HTTPException(status_code=422, detail="Group Id is required for group story")
    
    try:
        cursor.execute("""
            INSERT INTO stories (uploader_id, content, visibility, group_id)
            VALUES (?, ?, ?, ?)
    """, (uploader_id, content, visibility.value. group_id))
    
        new_story_id = cursor.lastrowid
        conn.commit()
    except sqlite3.Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    
    conn.close()

    return {
        "message": "Story uploaded successfully",
        "story_id": new_story_id,
        "visibility": visibility.value
    }