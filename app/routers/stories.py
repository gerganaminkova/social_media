import sqlite3
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from database import get_db_connection
from models import Visibility, Role, ReactionType
from utils import get_current_user, get_optional_user

router = APIRouter()


@router.post("/create-story")
def create_story(
    content: str,
    visibility: Visibility,
    group_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
):
    uploader_id = current_user["id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    if visibility == Visibility.GROUP and group_id is None:
        conn.close()
        raise HTTPException(
            status_code=422, detail="Group Id is required for group story"
        )

    try:
        cursor.execute(
            """
            INSERT INTO stories (uploader_id, content, visibility, group_id)
            VALUES (?, ?, ?, ?)
            """,
            (uploader_id, content, visibility.value, group_id),
        )

        new_story_id = cursor.lastrowid
        conn.commit()
    except sqlite3.Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    conn.close()

    return {
        "message": "Story uploaded successfully",
        "story_id": new_story_id,
        "visibility": visibility.value,
    }


@router.post("/react-to-story")
def react_to_story(
    story_id: int, emoji: ReactionType, current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM stories WHERE id = ?",
        (story_id,),
    )
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Story not found")

    try:
        cursor.execute(
            """
            INSERT INTO stories_reaction (user_id , story_id, emoji)
            VALUES (?, ?, ?)
            """,
            (user_id, story_id, emoji.value),
        )
        conn.commit()
    except sqlite3.Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    conn.close()
    return {"message": f"Reacted with {emoji.value}"}


@router.delete("/delete-story")
def delete_story(story_id: int, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    user_role = current_user["role"]

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT uploader_id FROM stories WHERE id = ?", (story_id,))
    story = cursor.fetchone()

    if not story:
        conn.close()
        raise HTTPException(status_code=404, detail="Story not found")

    is_owner = dict(story)["uploader_id"] == user_id
    is_admin = user_role == "admin"

    if not is_owner and not is_admin:
        conn.close()
        raise HTTPException(
            status_code=403, detail="You can only delete your own stories"
        )

    cursor.execute(
        "DELETE FROM stories WHERE id = ?",
        (story_id,),
    )
    conn.commit()
    conn.close()

    return {"message": "Story deleted successfully"}


@router.get("/get-stories")
def get_stories(current_user: Optional[dict] = Depends(get_optional_user)):
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if current_user:
        viewer_id = current_user["id"]
    else:
        viewer_id = None

    query = """
    SELECT
        s.id,
        s.content,
        s.timestamp,
        s.visibility,
        s.uploader_id,
        u.name as uploader_name,
        u.profile_image
    FROM stories s
    JOIN users u ON s.uploader_id = u.id
    WHERE
        s.timestamp > datetime('now', '-1 day')
        AND (
            s.uploader_id = ?
            OR s.visibility = 'public'
            OR (s.visibility = 'friends' AND EXISTS (
                SELECT 1 FROM friends f
                WHERE ((f.user_id = s.uploader_id AND f.friend_id = ?)
                    OR (f.user_id = ? AND f.friend_id = s.uploader_id))
                    AND f.status = 'accepted'
            ))
            OR (s.visibility = 'group' AND EXISTS (
                SELECT 1 FROM groups_users gu
                WHERE gu.group_id = s.group_id AND gu.user_id = ?
            ))
        )
    ORDER BY s.timestamp DESC
    """
    cursor.execute(query, (viewer_id, viewer_id, viewer_id, viewer_id))

    rows = cursor.fetchall()
    stories_list = []

    for row in rows:
        story = dict(row)

        cursor.execute(
            """
            SELECT emoji, COUNT(*) as count
            FROM stories_reaction
            WHERE story_id = ?
            GROUP BY emoji
            """,
            (story["id"],),
        )

        reactions = [dict(r) for r in cursor.fetchall()]
        story["reactions"] = reactions
        stories_list.append(story)

    conn.close()

    return {"stories": stories_list}
