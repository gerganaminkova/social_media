from enum import Enum
from pydantic import BaseModel


class Role(str, Enum):
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


class ReactionType(str, Enum):
    WOW = "😲"
    LOVE = "❤️"
    FIRE = "🔥"
    LAUGH = "😂"
    CLAP = "👏"


class UserRegister(BaseModel):
    name: str
    password: str
    role: Role
