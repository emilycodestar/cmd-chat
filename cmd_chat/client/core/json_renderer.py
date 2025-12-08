import json
from cmd_chat.client.core.abs.abs_renderer import ClientRenderer

class JsonClientRenderer(ClientRenderer):
    """JSON mode renderer - outputs raw JSON for programmatic use."""
    
    def print_message(self, message: str) -> str:
        return message
    
    def clear_console(self):
        pass  # No clearing in JSON mode
    
    def print_ip(self, ip: str) -> str:
        return ip
    
    def print_username(self, username: str) -> str:
        return username
    
    def print_chat(self, response) -> None:
        """Output chat data as JSON."""
        output = {
            "users": [
                {
                    "ip": user.split(',')[0],
                    "username": user.split(",")[1] if "," in user else user
                }
                for user in response.get("users_in_chat", [])
            ],
            "messages": [
                {
                    "text": self._decrypt(msg.get("text", msg) if isinstance(msg, dict) else msg),
                    "timestamp": msg.get("timestamp") if isinstance(msg, dict) else None,
                    "sequence": msg.get("sequence") if isinstance(msg, dict) else None,
                    "username": msg.get("username") if isinstance(msg, dict) else None
                }
                for msg in response.get("messages", [])
            ],
            "room_id": response.get("room_id", "default"),
            "last_sequence": response.get("last_sequence", 0)
        }
        print(json.dumps(output, indent=2))

