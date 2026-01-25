import sqlite3

# Establish a connection to the SQLite database
conn = sqlite3.connect("social_media.db")
conn.execute("PRAGMA foreign_keys = ON")

# Create users table
conn.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('user', 'admin', 'guest')),
        profile_image TEXT
    )
""")

# Create friends table
conn.execute("""
    CREATE TABLE IF NOT EXISTS friends(
        user_id REFERENCES users(id) ON DELETE CASCADE,
        friend_id REFERENCES users(id) ON DELETE CASCADE,
        status TEXT DEFAULT 'PENDING',
        PRIMARY KEY (user_id, friend_id)
    )
""")

# Create groups table
conn.execute("""
    CREATE TABLE IF NOT EXISTS groups(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        owner_id REFERENCES users(id) ON DELETE CASCADE
    )
""")

# Create groups_users table
conn.execute("""
    CREATE TABLE IF NOT EXISTS groups_users(
        group_id REFERENCES groups(id) ON DELETE CASCADE,
        user_id REFERENCES users(id) ON DELETE CASCADE
    )
"""
)

# Create posts table
conn.execute("""
    CREATE TABLE IF NOT EXISTS posts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        post_type TEXT NOT NULL CHECK(post_type IN ('text', 'picture')),
        content TEXT NOT NULL,
        visibility TEXT NOT NULL CHECK(visibility IN ('public', 'friends' , 'group')),
        group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE
    )
""")

# Create likes table
conn.execute("""
    CREATE TABLE IF NOT EXISTS likes(
        user_id REFERENCES users(id) ON DELETE CASCADE,
        post_id REFERENCES posts(id) ON DELETE CASCADE,
        PRIMARY KEY (user_id, post_id)
    )
""")

# Create comments table
conn.execute("""
    CREATE TABLE IF NOT EXISTS comments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id REFERENCES users(id) ON DELETE CASCADE,
        post_id REFERENCES posts(id) ON DELETE CASCADE,
        content TEXT NOT NULL
    )
""")

# Create tags table
conn.execute("""
    CREATE TABLE IF NOT EXISTS tags(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL
    )
""")

# Create posts_tags table (many-to-many)
conn.execute("""
    CREATE TABLE IF NOT EXISTS posts_tags(
        post_id REFERENCES posts(id) ON DELETE CASCADE,
        tags_id REFERENCES tags(id) ON DELETE CASCADE
    )
""")

# Create messages table
conn.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        receiver_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        content TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")


