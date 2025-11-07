import ast
from sanic import Websocket
from cmd_chat.server.models import Message


async def _get_bytes_and_serialize(
    ws: Websocket
) -> dict:
    return ast.literal_eval(await ws.recv())


async def _check_ws_for_close_status(
    response: dict,
    ws: Websocket
) -> None:
    if "action" in response.keys():
        if response["action"] == "close":
            await ws.close()


async def _generate_new_message(
    message: str
) -> Message:
    return Message(message = message)


async def _generate_update_payload(
    memory_msgs: list[Message],
    users_structure: dict
) -> str:
    return str({
        "messages": [i.message for i in memory_msgs], 
        "users_in_chat": list(users_structure.keys())
    })


