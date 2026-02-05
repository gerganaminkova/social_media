import sqlite3
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from database import get_db_connection
from models import UserRegister, Role
from utils import create_access_token

router = APIRouter(tags=["Authentication"])


@router.post("/auth/register")
def register(user: UserRegister):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE name = ?", (user.name,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username taken")

    if user.role == Role.ADMIN:
        cursor.execute("SELECT id FROM users WHERE role = 'admin'")
        admin_user_row = cursor.fetchone()

        if admin_user_row is not None:
            conn.close()
            raise HTTPException(
                status_code=422,
                detail="An admin user already exists. You cannot register as admin.",
            )
    try:
        cursor.execute(
            """
                INSERT INTO users (name, password, role, profile_image)
                VALUES (?, ?, ?, ?)
            """,
            (user.name, user.password, user.role.value, None),
        )

        conn.commit()
    except sqlite3.Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    conn.close()

    return {
        "message": f"User {user.name} created successfully with role {user.role.value}"
    }


@router.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE name = ?", (form_data.username,))
    user = cursor.fetchone()

    if not user or form_data.password != dict(user)["password"]:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid credentials")

    conn.close()

    access_token = create_access_token(
        data={
            "sub": dict(user)["name"],
            "user_id": dict(user)["id"],
            "role": dict(user)["role"],
        }
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.delete("/force-delete-user")
def force_delete_user(name: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE name = ?", (name,))
    conn.commit()
    conn.close()

    return {"message": f"ЧАО! Потребител '{name}' беше изтрит завинаги."}
