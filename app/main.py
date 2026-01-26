from fastapi import FastAPI
from routers import users, friends, groups, posts, chat
from routers import users, friends, groups, posts, chat, stories

app = FastAPI()

app.include_router(users.router)
app.include_router(friends.router)
app.include_router(groups.router)
app.include_router(posts.router)
app.include_router(chat.router)
app.include_router(stories.router)

@app.get("/")
def root():
    return {"message": "Hello, World!"}