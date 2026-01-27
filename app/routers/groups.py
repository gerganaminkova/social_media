import sqlite3
from fastapi import APIRouter, HTTPException, Depends
from database import get_db_connection
from models import Role

router = APIRouter()


@router.post("/create-group")
def create_group(name: str, owner_id: int, member_ids: list[int]):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
                   SELECT role FROM users WHERE id = ?
    """,
        (owner_id,),
    )
    owner_role_row = cursor.fetchone()

    if not owner_role_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Owner not found")

    owner_role = dict(owner_role_row)["role"]

    if owner_role == "guest":
        conn.close()
        raise HTTPException(
            status_code=422, detail="Guests are not allowed to create groups"
        )

    cursor.execute(
        """
        INSERT INTO groups (name, owner_id) VALUES (?, ?)
    """,
        (name, owner_id),
    )

    new_group_id = cursor.lastrowid
    for member_id in member_ids:
        cursor.execute(
            """
            INSERT INTO groups_users (group_id, user_id) VALUES (?, ?)
        """,
            (new_group_id, member_id),
        )

    conn.commit()
    conn.close()

    return {"message": "Group created successfully"}


@router.delete("/remove-group-member")
def remove_group_member(group_id: int, user_id: int, owner_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
                   SELECT owner_id FROM groups WHERE id = ?
    """,
        (group_id,),
    )
    group_row = cursor.fetchone()

    if not group_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Group not found")

    if dict(group_row)["owner_id"] != owner_id:
        conn.close()
        raise HTTPException(
            status_code=403, detail="Only the group owner can remove members"
        )

    cursor.execute(
        """
        DELETE FROM groups_users 
        WHERE group_id = ? AND user_id = ?
    """,
        (group_id, user_id),
    )

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(
            status_code=404, detail="User is not a member of this group"
        )

    conn.commit()
    conn.close()

    return {"message": "Member removed from group successfully"}


@router.delete("/delete-group")
def delete_group(group_id: int, owner_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
                   SELECT owner_id FROM groups WHERE id = ?
    """,
        (group_id,),
    )
    group_row = cursor.fetchone()

    if not group_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Group not found")

    if dict(group_row)["owner_id"] != owner_id:
        conn.close()
        raise HTTPException(
            status_code=403, detail="Only the group owner can delete the group"
        )

    cursor.execute(
        """
                   DELETE FROM groups WHERE id = ?
    """,
        (group_id,),
    )

    conn.commit()
    conn.close()

    return {"message": "Group deleted successfully"}


@router.post("/add-member")
def add_member_to_group(group_id: int, admin_id: int, new_member_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT owner_id FROM groups WHERE id = ?", (group_id,))
    group = cursor.fetchone()

    if not group:
        conn.close()
        raise HTTPException(status_code=404, detail="Group not found")

    if dict(group)["owner_id"] != admin_id:
        conn.close()
        raise HTTPException(
            status_code=403, detail="Only the group owner can add members"
        )

    cursor.execute("SELECT id FROM users WHERE id = ?", (new_member_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="User to add not found")

    cursor.execute(
        """
        SELECT 1 FROM groups_users 
        WHERE group_id = ? AND user_id = ?
    """,
        (group_id, new_member_id),
    )

    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="User is already in the group")

    try:
        cursor.execute(
            """
            INSERT INTO groups_users (group_id, user_id)
            VALUES (?, ?)
        """,
            (group_id, new_member_id),
        )
        conn.commit()
    except sqlite3.Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    conn.close()
    return {"message": "User added to group successfully"}
