"""Event types that can be received from the server."""
from enum import Enum


class EventType(Enum):
    """Event types that can be received from the server."""

    BROADCAST_START = "broadcastStart"
    BROADCAST_STOP = "broadcastStop"
    CHAT_MESSAGE = "chatMessage"
    FANCLUB_JOIN = "fanclubJoin"
    FOLLOW = "follow"
    MEDIA_PURCHASE = "mediaPurchase"
    PRIVATE_MESSAGE = "privateMessage"
    ROOM_SUBJECT_CHANGE = "roomSubjectChange"
    TIP = "tip"
    UNFOLLOW = "unfollow"
    USER_ENTER = "userEnter"
    USER_LEAVE = "userLeave"
