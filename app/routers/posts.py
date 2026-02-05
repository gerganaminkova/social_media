import sqlite3
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from database import get_db_connection
from models import PostType, Visibility
from utils import get_current_user, get_optional_user

router = APIRouter()


@router.post("/create-post")
def create_post(
    post_type: PostType,
    content: str,
    visibility: Visibility,
    group_id: Optional[int] = None,
    tags: list[str] = Query(default=[]),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    # validation to prevent the visibility when it is a group post
    if visibility == Visibility.GROUP and group_id is None:
        conn.close()
        raise HTTPException(
            status_code=422, detail="Group ID is required for group visibility"
        )

    # adding a post
    cursor.execute(
        """
        INSERT INTO posts (user_id , post_type, content, visibility, group_id)
        VALUES (?, ?, ?, ?, ?)
    """,
        (user_id, post_type.value, content, visibility.value, group_id),
    )

    new_post = cursor.lastrowid

    for tags_text in tags:
        cursor.execute(
            """
            SELECT id FROM tags WHERE content = ?
        """,
            (tags_text,),
        )
        existing_tag = cursor.fetchone()

        if existing_tag:
            tag_id = dict(existing_tag)["id"]
        else:
            cursor.execute(
                """
                INSERT INTO tags (content) VALUES (?)
            """,
                (tags_text,),
            )
            tag_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO posts_tags (post_id, tags_id) VALUES (?, ?)
        """,
            (new_post, tag_id),
        )

    conn.commit()
    conn.close()

    return {
        "message": f"User {user_id} posted successfully a {post_type.value}",
    }


@router.delete("/delete-post")
def delete_post(post_id: int, current_user: dict = Depends(get_current_user)):

    user_id = current_user["id"]
    user_role = current_user["role"]

    conn = get_db_connection()
    cursor = conn.cursor()

    # validate that the post exists
    cursor.execute(
        """
        SELECT user_id FROM posts WHERE id = ?
    """,
        (post_id,),
    )
    post_row = cursor.fetchone()

    if post_row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Post not found")

    post_user_id = dict(post_row)["user_id"]

    if user_id != post_user_id and user_role != "admin":
        conn.close()
        raise HTTPException(
            status_code=403, detail="You are not allowed to delete this post"
        )
    cursor.execute(
        """
                   DELETE FROM posts WHERE id = ?""",
        (post_id,),
    )
    conn.commit()
    conn.close()

    return {"message": f"Post {post_id} deleted successfully"}


@router.get("/get-post/{post_id}")
def get_post(post_id: int, current_user: Optional[dict] = Depends(get_optional_user)):
    conn = get_db_connection()
    cursor = conn.cursor()

    if current_user:
        viewer_id = current_user["id"]
        viewer_role = current_user["role"]
    else:
        viewer_id = None
        viewer_role = "guest"

    cursor.execute(
        """
        SELECT * FROM posts WHERE id = ?
    """,
        (post_id,),
    )
    post_row = cursor.fetchone()

    if not post_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Post not found")

    post = dict(post_row)
    author_id = post["user_id"]
    visibility = post["visibility"]
    group_id = post["group_id"]
    # validate if you are an admin or author of the post
    if viewer_role == "admin" or viewer_id == author_id:
        pass
    # validate if itt is a public post
    elif visibility == "public":
        pass
    # validate that that only friends can see it
    elif visibility == "friends":
        if viewer_role == "guest":
            conn.close()
            raise HTTPException(
                status_code=403, detail="Guests cannot view friends-only posts"
            )

        # validate if they are friends
        cursor.execute(
            """
                        SELECT 1 FROM friends 
                        WHERE ((user_id = ? AND friend_id = ?) 
                        OR (user_id = ? AND friend_id = ?))
                        AND status = 'accepted'
                    """,
            (author_id, viewer_id, viewer_id, author_id),
        )

        if not cursor.fetchone():
            conn.close()
            raise HTTPException(
                status_code=403, detail="You must be a friend to view this post"
            )
    # validate if it is a group
    elif visibility == "group":

        if viewer_role == "guest":
            conn.close()
            raise HTTPException(
                status_code=403, detail="Guests cannot view group posts"
            )

        if not group_id:
            conn.close()
            raise HTTPException(
                status_code=500, detail="Invalid post data: Missing group ID"
            )

        # validate that the viewer is a part of the group
        cursor.execute(
            """
            SELECT 1 FROM groups_users 
            WHERE group_id = ? AND user_id = ?
        """,
            (group_id, viewer_id),
        )

        if not cursor.fetchone():
            conn.close()
            raise HTTPException(
                status_code=403,
                detail="You must be a member of the group to view this post",
            )

    cursor.execute(
        """
            SELECT t.content FROM tags t 
            JOIN posts_tags pt ON t.id = pt.tags_id 
            WHERE pt.post_id = ?
        """,
        (post_id,),
    )

    tags_rows = cursor.fetchall()
    tags_list = [dict(row)["content"] for row in tags_rows]

    conn.close()

    return {"post_data": post, "tags": tags_list}


@router.put("/update-post/{post_id}")
def update_post(
    post_id: int,
    content: str = None,
    visibility: Visibility = None,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT user_id FROM posts WHERE id = ?
    """,
        (post_id,),
    )
    post_row = cursor.fetchone()

    if not post_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Post not found")

    author_id = dict(post_row)["user_id"]

    if author_id != user_id:
        conn.close()
        raise HTTPException(status_code=403, detail="You can only edit your own posts!")

    if content is not None:
        cursor.execute(
            """
            UPDATE posts SET content = ? WHERE id = ?
    """,
            (content, post_id),
        )

    if visibility is not None:
        cursor.execute(
            """
            UPDATE posts SET visibility = ? WHERE id = ?
    """,
            (visibility.value, post_id),
        )

    conn.commit()
    conn.close()

    return {"message": f"Post {post_id} updated successfully"}
