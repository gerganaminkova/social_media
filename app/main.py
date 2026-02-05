from fastapi import FastAPI
from routers import friends, groups, posts, chat, stories, auth

app = FastAPI()

app.include_router(auth.router)
app.include_router(friends.router)
app.include_router(groups.router)
app.include_router(posts.router)
app.include_router(chat.router)
app.include_router(stories.router)


@app.get("/")
def root():
    return {"message": "Hello, World!"}
