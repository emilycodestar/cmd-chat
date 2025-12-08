import json
import time
from sanic import Websocket
from cmd_chat.server.models import Message

# Global sequence counter for messages
MESSAGE_SEQUENCE = 0

async def _get_bytes_and_serialize(
    ws: Websocket
) -> dict:
    raw = await ws.recv()
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    
    # Payload size validation (max 1MB)
    if len(raw) > 1_048_576:
        return {"error": "message_too_large"}
    
    return json.loads(raw)


async def _check_ws_for_close_status(
    response: dict,
    ws: Websocket
) -> None:
    if "action" in response.keys():
        if response["action"] == "close":
            await ws.close()


async def _generate_new_message(
    message: str,
    username: str | None = None,
    room_id: str | None = None
) -> Message:
    global MESSAGE_SEQUENCE
    MESSAGE_SEQUENCE += 1
    return Message(
        message=message,
        timestamp=time.time(),
        sequence=MESSAGE_SEQUENCE,
        room_id=room_id or "default",
        username=username
    )


async def _generate_update_payload(
    memory_msgs: list[Message],
    users_structure: dict,
    room_id: str = "default",
    last_sequence: int = 0,
    user_rooms: dict | None = None
) -> str:
    """Generate update payload with delta updates support."""
    # Filter messages by room and sequence
    room_messages = [
        msg for msg in memory_msgs
        if msg.room_id == room_id and (msg.sequence or 0) > last_sequence
    ]
    
    # Filter users by room if user_rooms is provided
    if user_rooms:
        users_in_room = [
            key for key, room in user_rooms.items() 
            if room == room_id and key in users_structure
        ]
    else:
        users_in_room = list(users_structure.keys())
    
    return json.dumps({
        "messages": [
            {
                "text": msg.message,
                "timestamp": msg.timestamp,
                "sequence": msg.sequence,
                "username": msg.username
            }
            for msg in room_messages
        ],
        "users_in_chat": users_in_room,
        "room_id": room_id,
        "last_sequence": max([msg.sequence or 0 for msg in memory_msgs if msg.room_id == room_id], default=0)
    })


async def _generate_full_update_payload(
    memory_msgs: list[Message],
    users_structure: dict,
    room_id: str = "default",
    user_rooms: dict | None = None
) -> str:
    """Generate full update payload (for initial connection)."""
    room_messages = [msg for msg in memory_msgs if msg.room_id == room_id]
    
    # Filter users by room if user_rooms is provided
    if user_rooms:
        users_in_room = [
            key for key, room in user_rooms.items() 
            if room == room_id and key in users_structure
        ]
    else:
        users_in_room = list(users_structure.keys())
    
    return json.dumps({
        "messages": [
            {
                "text": msg.message,
                "timestamp": msg.timestamp,
                "sequence": msg.sequence,
                "username": msg.username
            }
            for msg in room_messages
        ],
        "users_in_chat": users_in_room,
        "room_id": room_id,
        "last_sequence": max([msg.sequence or 0 for msg in room_messages], default=0)
    })
