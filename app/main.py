import sqlite3
from enum import Enum
from typing import Optional

from fastapi import FastAPI, HTTPException, Query

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Hello, World!"}


class Role(Enum):
    GUEST = "guest"
    USER = "user"
    ADMIN = "admin"


class PostType(Enum):
    TEXT = "text"
    PICTURE = "picture"


class Visibility(Enum):
    PUBLIC = "public"
    FRIENDS = "friends"
    GROUP = "group"

class FriendRequestAction(Enum):
    ACCEPT = "accept"
    DECLINE = "decline"


def get_db_connection():
    conn = sqlite3.connect("social_media.db")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


@app.post("/create-user")
def create_user(name: str, password: str, role: Role, profile_image: str = None):
    conn = get_db_connection() 
    cursor = conn.cursor()

    if role == Role.ADMIN:
        cursor.execute("""
            SELECT * FROM users WHERE role = 'admin'
        """)
        admin_user_row = cursor.fetchone()
        if not admin_user_row is None:
            conn.close()
            raise HTTPException(status_code=422, detail="An admin user already exists")

    cursor.execute("""
        INSERT INTO users (name, password, role, profile_image) VALUES (?, ?, ?, ?)
    """, (name, password, role.value, profile_image))
    
    conn.commit()
    conn.close()

    return {
        "message": f"User {name} created successfully with role {role.value}",
    }

@app.post("/send-friend-request")
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

@app.post("/respond-friend-request")
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

@app.get("/get-my-friends/{user_id}")
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

@app.delete("/remove-friend")
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



@app.post("/create-group")
def create_group(name: str, owner_id: int, member_ids: list[int]):
    conn = get_db_connection() 
    cursor = conn.cursor()

    cursor.execute("""
                   SELECT role FROM users WHERE id = ?
    """, (owner_id,))
    owner_role_row = cursor.fetchone()
    
    if not owner_role_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Owner not found")

    owner_role = dict(owner_role_row)["role"]

    if owner_role == 'guest':
        conn.close()
        raise HTTPException(status_code=422, detail="Guests are not allowed to create groups")

    cursor.execute("""
        INSERT INTO groups (name, owner_id) VALUES (?, ?)
    """, (name, owner_id))
    
    new_group_id = cursor.lastrowid 


    for member_id in member_ids:
        cursor.execute("""
            INSERT INTO groups_users (group_id, user_id) VALUES (?, ?)
        """, (new_group_id, member_id))

    conn.commit()
    conn.close()

    return {"message": "Group created successfully"}
            

@app.delete("/remove-group-member")
def remove_group_member(group_id: int, user_id: int, owner_id: int):   
    conn = get_db_connection() 
    cursor = conn.cursor()

    cursor.execute("""
                   SELECT owner_id FROM groups WHERE id = ?
    """, (group_id,))
    group_row = cursor.fetchone()

    if not group_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Group not found")

    if dict(group_row)["owner_id"] != owner_id:
        conn.close()
        raise HTTPException(status_code=403, detail="Only the group owner can remove members")

    cursor.execute("""
        DELETE FROM groups_users 
        WHERE group_id = ? AND user_id = ?
    """, (group_id, user_id))

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="User is not a member of this group")

    conn.commit()
    conn.close()

    return {"message": "Member removed from group successfully"}


@app.delete("/delete-group")
def delete_group(group_id: int, owner_id: int):
    conn = get_db_connection() 
    cursor = conn.cursor()

    cursor.execute("""
                   SELECT owner_id FROM groups WHERE id = ?
    """, (group_id,))
    group_row = cursor.fetchone()

    if not group_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Group not found")

    if dict(group_row)["owner_id"] != owner_id:
        conn.close()
        raise HTTPException(status_code=403, detail="Only the group owner can delete the group")

    cursor.execute("""
                   DELETE FROM groups WHERE id = ?
    """, (group_id,))

    conn.commit()
    conn.close()

    return {"message": "Group deleted successfully"}


@app.post("/create-post")
def create_post(
    user_id: int, 
    post_type: PostType, 
    content: str,
    visibility: Visibility, 
    group_id: Optional[int] = None, 
    tags: list[str] = Query(default=[])
):
    conn = get_db_connection() 
    cursor = conn.cursor()

    # validation to prevent guests from posting 
    cursor.execute("""
        SELECT role FROM users WHERE id = ? 
    """, (user_id,))
    user_role_row = cursor.fetchone()
    user_role = dict(user_role_row)["role"]
    print(user_role)

    if user_role == 'guest':
        conn.close()
        raise HTTPException(status_code=422, detail="Guests are not allowed to post!")

    # validation to prevent the visibility when it is a group post 
    if visibility == Visibility.GROUP and group_id is None:
        conn.close()
        raise HTTPException(status_code=422, detail="Group ID is required for group visibility")

    # validation that the user exists 
    if not user_id:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    # adding a post 
    cursor.execute("""
        INSERT INTO posts (user_id , post_type, content, visibility, group_id)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, post_type.value, content, visibility.value, group_id))

    new_post = cursor.lastrowid

    for tags_text in tags:
        cursor.execute("""
            SELECT id FROM tags WHERE content = ?
        """, (tags_text,))
        existing_tag = cursor.fetchone()

        if existing_tag:
            tag_id = dict(existing_tag)["id"]
        else:
            cursor.execute("""
                INSERT INTO tags (content) VALUES (?)
            """, (tags_text,))
            tag_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO posts_tags (post_id, tags_id) VALUES (?, ?)
        """, (new_post, tag_id))

    conn.commit()
    conn.close()

    return {
        "message": f"User {user_id} posted successfully a {post_type.value}",
    }


@app.delete("/delete-post")
def delete_post(user_id: int, post_id: int):
    conn = get_db_connection() 
    cursor = conn.cursor()

    # validate that the post exists 
    cursor.execute("""
        SELECT user_id FROM posts WHERE id = ?
    """, (post_id,))
    post_row = cursor.fetchone()

    if post_row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Post not found")

    # validate that the user own the post    
    post_user_id = dict(post_row)["user_id"]
    cursor.execute("""
                   SELECT role FROM users WHERE id = ?
    """, (user_id,))
    user_row = cursor.fetchone()

    if not user_row:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    user_role = dict(user_row)["role"]

    if user_id != post_user_id and user_role != 'admin':
        conn.close()
        raise HTTPException(status_code=403, detail="You are not allowed to delete this post")

    cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()

    return {"message": f"Post {post_id} deleted successfully"}


@app.get("/get-post/{post_id}")
def get_post(post_id: int, viewer_id: int):
    conn = get_db_connection() 
    cursor = conn.cursor()

    cursor.execute("""
        SELECT role FROM users WHERE id = ?
    """, (viewer_id,))
    viewer_row = cursor.fetchone()

    if not viewer_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Viewer user not found")

    viewer_role = dict(viewer_row)["role"]

    cursor.execute("""
        SELECT * FROM posts WHERE id = ?
    """, (post_id,))
    post_row = cursor.fetchone()

    if not post_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Post not found")

    post = dict(post_row)
    author_id = post["user_id"]
    visibility = post["visibility"]
    group_id = post["group_id"]
# validate if you are an admin or author of the post
    if viewer_role == 'admin' or viewer_id == author_id:
        pass 
# validate if itt is a public post 
    elif visibility == 'public':
        pass 
# validate that that only friends can see it     
    elif visibility == 'friends':
        if viewer_role == 'guest':
            conn.close()
            raise HTTPException(status_code=403, detail="Guests cannot view friends-only posts")

# validate if they are friends
    cursor.execute("""
                SELECT 1 FROM friends 
                WHERE ((user_id = ? AND friend_id = ?) 
                OR (user_id = ? AND friend_id = ?))
                AND status = 'accepted'
            """, (author_id, viewer_id, viewer_id, author_id))
            
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=403, detail="You must be a friend to view this post")
# validate if it is a group
    elif visibility == 'group':
        
        if viewer_role == 'guest':
            conn.close()
            raise HTTPException(status_code=403, detail="Guests cannot view group posts")
        
        if not group_id: 
             conn.close()
             raise HTTPException(status_code=500, detail="Invalid post data: Missing group ID")

# validate that the vewer is a part of the group
        cursor.execute("""
            SELECT 1 FROM groups_users 
            WHERE group_id = ? AND user_id = ?
        """, (group_id, viewer_id))
        
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=403, detail="You must be a member of the group to view this post")

        cursor.execute("""
            SELECT t.content FROM tags t 
            JOIN posts_tags pt ON t.id = pt.tags_id 
            WHERE pt.post_id = ?
        """, (post_id,))

    tags_rows = cursor.fetchall()
    tags_list = [dict(row)["content"] for row in tags_rows]

    conn.close()

    return {
        "post_data": post,
        "tags": tags_list
    }

@app.put("/update-post/{post_id}")
def update_post(
    post_id: int, 
    user_id: int, 
    content: str = None, 
    visibility: Visibility = None
):
    conn = get_db_connection() 
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id FROM posts WHERE id = ?
    """, (post_id,))
    post_row = cursor.fetchone()

    if not post_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Post not found")

    author_id = dict(post_row)["user_id"]

    if author_id != user_id:
        conn.close()
        raise HTTPException(status_code=403, detail="You can only edit your own posts!")

    if content is not None:
        cursor.execute("""
            UPDATE posts SET content = ? WHERE id = ?
    """, (content, post_id))

    if visibility is not None:
        cursor.execute("""
            UPDATE posts SET visibility = ? WHERE id = ?
    """, (visibility.value, post_id))

    conn.commit()
    conn.close()

    return {"message": f"Post {post_id} updated successfully"}


@app.post("/toggle-like")
def toggle_like(post_id: int, user_id: int):
    conn = get_db_connection() 
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM posts WHERE id = ?
    """, (post_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Post not found")

    cursor.execute("""
        SELECT id FROM users WHERE id = ?
    """, (user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    cursor.execute("""
                   SELECT * FROM likes WHERE user_id = ? AND post_id = ?
                   """, (user_id, post_id))
    existing_like = cursor.fetchone()

    if existing_like:
        cursor.execute("""
                        DELETE FROM likes WHERE user_id = ? AND post_id = ?
                    """, (user_id, post_id))
        message = "Like removed"
        liked = False
    else:
        cursor.execute("""
                        INSERT INTO likes(user_id, post_id) VALUES(?,?)
                    """, (user_id, post_id))
        message = "Post liked"
        liked = True

    conn.commit()

    cursor.execute("""
                    SELECT COUNT(*) as count FROM likes WHERE post_id = ?
                   """, (post_id,))
    total_likes = dict(cursor.fetchone())["count"]

    conn.close()
    return {"message": message, "is_liked": liked, "total_likes": total_likes}


@app.post("/add-comment/{post_id}")
def add_comment(post_id: int, user_id: int, content: str):
    conn = get_db_connection() 
    cursor = conn.cursor()

    cursor.execute("""          
                    SELECT id FROM posts WHERE id = ?
                    """, (post_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Post not found")

    cursor.execute("""
        SELECT id FROM users WHERE id = ?
    """, (user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    cursor.execute("""
        INSERT INTO comments (user_id, post_id, content) 
        VALUES (?, ?, ?)
    """, (user_id, post_id, content))

    new_comment_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "message": "Comment added successfully",
        "comment_id": new_comment_id,
        "content": content
    }


@app.get("/get-comments/{post_id}")
def get_comments(post_id: int):
    conn = get_db_connection() 
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM posts WHERE id = ?", (post_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Post not found")

    cursor.execute("""
        SELECT c.id, c.content, u.name as author_name 
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.post_id = ?
    """, (post_id,))

    rows = cursor.fetchall()
    comments_list = [dict(row) for row in rows]

    conn.close()

    return {
        "post_id": post_id,
        "comments": comments_list
    }

@app.post("/send-message")
def send_message(sender_id: int, receiver_id: int, content: str ):
    conn = get_db_connection() 
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM users WHERE id = ?
    """,(sender_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="sender not found")
    
    cursor.execute("""
       SELECT id FROM users WHERE id = ?
    """,(receiver_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="receiver not found")
    
    cursor.execute("""
        SELECT 1 FROM friends 
        WHERE ((user_id = ? AND friend_id = ?) 
           OR (user_id = ? AND friend_id = ?))
          AND status = 'accepted'
    """,(sender_id, receiver_id, receiver_id, sender_id))

    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=403, detail="You can only message a friend!")
    
    cursor.execute("""
        INSERT INTO messages(sender_id, receiver_id, content) VALUES (?, ?, ?)
    """,(sender_id, receiver_id, content))

    conn.commit()
    conn.close()

    return{"message:" "Message sent successfully"}

@app.get("/get-chat")
def get_chat(user1_id: int, user2_id: int):
    conn = get_db_connection() 
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM users WHERE id = ?
    """,(user1_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="sender not found")
    
    cursor.execute("""
       SELECT id FROM users WHERE id = ?
    """,(user2_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="sender not found")
    
    cursor.execute("""
        SELECT m.content, m.timestamp, u.name as sender_name
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE (m.sender_id = ? AND m.receiver_id = ?)
           OR (m.sender_id = ? AND m.receiver_id = ?)
        ORDER BY m.timestamp ASC
    """,(user1_id, user2_id, user2_id, user1_id))

    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return{
        "chat_participants": [user1_id, user2_id,],
        "messages": messages
    }