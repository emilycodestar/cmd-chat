from colorama import Fore
import os

COLORS = {
    "text_color": Fore.WHITE,
    "my_username_color": Fore.MAGENTA,
    "ip_color": Fore.MAGENTA,
    "username_color": Fore.GREEN
}

RENDER_TIME = float(os.getenv("CLIENT_RENDER_TIME", "0.1"))
MESSAGES_TO_SHOW = int(os.getenv("CLIENT_MESSAGES_TO_SHOW", "10"))
ENABLE_LOCAL_HISTORY = os.getenv("ENABLE_LOCAL_HISTORY", "false").lower() == "true"
RENDERER_MODE = os.getenv("RENDERER_MODE", "rich")  # rich, minimal, json