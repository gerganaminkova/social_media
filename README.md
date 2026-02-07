# Social Media API

 Social Media API built with **FastAPI** and **SQLite**. Supports user authentication, posts with visibility controls, friend management, group chat, direct messaging, and stories with emoji reactions.

## Features

- **Authentication** — Register and login with JWT-based token authentication
- **Posts** — Create, read, update, and delete posts with text types
- **Visibility Controls** — Posts and stories can be public, friends-only, or group-only
- **Friends** — Send, accept, and decline friend requests; remove friends
- **Groups** — Create groups, add/remove members, group-only content
- **Chat** — Direct messaging between friends with message history
- **Stories** — Time-limited stories (24h) with emoji reactions
- **Tagging** — Tag posts with custom tags

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/gerganaminkova/social_media.git
   cd social_media
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Initialize the database:**
   ```bash
   cd app
   python init_db.py
   ```

## Running the Application

Start the server from the `app/` directory:

```bash
cd app
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

Interactive API documentation (Swagger UI) is auto-generated at `http://127.0.0.1:8000/docs`.

## Running Tests

```bash
cd app
python -m pytest ../tests/ --cov=. -v
```

## API Endpoints Overview

| Method | Endpoint                   | Description                  |
|--------|----------------------------|------------------------------|
| POST   | `/auth/register`           | Register a new user          |
| POST   | `/auth/login`              | Login and receive JWT token  |
| POST   | `/create-post`             | Create a new post            |
| GET    | `/get-post/{post_id}`      | Get a post by ID             |
| PUT    | `/update-post/{post_id}`   | Update a post                |
| DELETE | `/delete-post`             | Delete a post                |
| POST   | `/send-friend-request`     | Send a friend request        |
| POST   | `/respond-friend-request`  | Accept or decline a request  |
| GET    | `/get-my-friends/{user_id}`| Get list of friends          |
| DELETE | `/remove-friend`           | Remove a friend              |
| POST   | `/create-group`            | Create a new group           |
| POST   | `/add-member`              | Add member to a group        |
| DELETE | `/remove-group-member`     | Remove member from a group   |
| DELETE | `/delete-group`            | Delete a group               |
| POST   | `/send-message`            | Send a direct message        |
| GET    | `/get-chat`                | Get chat history             |
| POST   | `/create-story`            | Create a new story           |
| POST   | `/react-to-story`          | React to a story with emoji  |
| DELETE | `/delete-story`            | Delete a story               |
| GET    | `/get-stories`             | Get visible stories          |

## Tech Stack

- **FastAPI** — Modern Python web framework
- **SQLite** — Lightweight relational database
- **JWT (python-jose)** — Token-based authentication
- **Pydantic** — Data validation and serialization
