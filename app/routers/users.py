from fastapi import APIRouter, HTTPException
from database import get_db_connection
from models import Role
import sqlite3


router = APIRouter()


@router.post("/create-user")
def create_user(name: str, password: str, role: Role, profile_image: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()

    if role == Role.ADMIN:
        cursor.execute(
            """
            SELECT * FROM users WHERE role = 'admin'
        """
        )
        admin_user_row = cursor.fetchone()
        if not admin_user_row is None:
            conn.close()
            raise HTTPException(status_code=422, detail="An admin user already exists")

    cursor.execute(
        """
        INSERT INTO users (name, password, role, profile_image) VALUES (?, ?, ?, ?)
    """,
        (name, password, role.value, profile_image),
    )

    conn.commit()
    conn.close()

    return {
        "message": f"User {name} created successfully with role {role.value}",
    }
