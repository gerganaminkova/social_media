import sys
import os
import sqlite3
import pytest
from fastapi.testclient import TestClient


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
sys.path.insert(0, os.path.dirname(__file__))


def create_tables(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'admin', 'guest')),
            profile_image TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS friends(
            user_id REFERENCES users(id) ON DELETE CASCADE,
            friend_id REFERENCES users(id) ON DELETE CASCADE,
            status TEXT DEFAULT 'PENDING',
            PRIMARY KEY (user_id, friend_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS groups(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            owner_id REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS groups_users(
            group_id REFERENCES groups(id) ON DELETE CASCADE,
            user_id REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            post_type TEXT NOT NULL CHECK(post_type IN ('text', 'picture')),
            content TEXT NOT NULL,
            visibility TEXT NOT NULL
                CHECK(visibility IN ('public', 'friends', 'group')),
            group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS likes(
            user_id REFERENCES users(id) ON DELETE CASCADE,
            post_id REFERENCES posts(id) ON DELETE CASCADE,
            PRIMARY KEY (user_id, post_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS comments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id REFERENCES users(id) ON DELETE CASCADE,
            post_id REFERENCES posts(id) ON DELETE CASCADE,
            content TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tags(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts_tags(
            post_id REFERENCES posts(id) ON DELETE CASCADE,
            tags_id REFERENCES tags(id) ON DELETE CASCADE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            receiver_id INTEGER NOT NULL
                REFERENCES users(id) ON DELETE CASCADE,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stories(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uploader_id INTEGER NOT NULL
                REFERENCES users(id) ON DELETE CASCADE,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            visibility TEXT NOT NULL
                CHECK(visibility IN ('public', 'friends', 'group')),
            group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stories_reaction(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            story_id INTEGER NOT NULL
                REFERENCES stories(id) ON DELETE CASCADE,
            emoji TEXT
        )
    """)
    conn.commit()


@pytest.fixture()
def client() -> TestClient:
    test_conn = sqlite3.connect(
        "file::memory:?cache=shared", uri=True
    )
    test_conn.row_factory = sqlite3.Row
    create_tables(test_conn)

    def get_test_db() -> sqlite3.Connection:
        conn = sqlite3.connect(
            "file::memory:?cache=shared", uri=True
        )
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    import database
    database.get_db_connection = get_test_db

    from main import app
    test_client = TestClient(app)

    yield test_client

    test_conn.close()
