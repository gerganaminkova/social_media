from enum import Enum


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
