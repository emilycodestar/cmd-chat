import os 
import platform

from rich.text import Text 
from rich.style import Style
from rich.console import Console 

from rich.table import Table
from cmd_chat.client.core.abs.abs_renderer import ClientRenderer
from cmd_chat.client.config import MESSAGES_TO_SHOW


console = Console(width=75)


class RichClientRenderer(ClientRenderer):

    def __get_os(self) -> str:
        """ checking what kind of platform you need
        """
        if "Linux" in str(platform.platform()):
            return "Linux"
        return "Windows"
    
    def print_message(self, message: str) -> Text:
        """ generating string with message in required format
        """
        # split only on the first ':' so message bodies containing ':' are preserved
        parts = message.split(":", 1)
        if parts[0] == self.username:
            return \
                Text(text=parts[0], style="bold") + \
                Text(text=": ", style="bold") + \
                Text(text=parts[1], style="underline")
        return \
            Text(text=parts[0], style="bold") + \
            Text(text=": ", style="bold") + \
            Text(text=parts[1], style="underline")

    def clear_console(self):
        # For windows clear command its cls
        # For linux clear command its clear
        if self.__get_os() == "Linux":
            os.system("clear")
        else:
            os.system("cls")

    def print_ip(
        self,
        ip: str
    ) -> str:
        return ip
    
    def print_username(
        self,
        username: str
    ) -> str:
        return username

    def print_chat(self, response) -> None:
        self.clear_console()
        for i, msg in enumerate(response["messages"][-MESSAGES_TO_SHOW:]):
            actual_message = self._decrypt(msg)
            if i == 0:
                console.print("Users in chat:", justify="left")
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("IP", style="dim", width=12)
                table.add_column("USERNAME")
                for user in response["users_in_chat"]:
                    table.add_row(
                        self.print_ip(user.split(',')[0]),
                        self.print_username(user.split(",")[1])
                    )
                console.print(table)
                console.print("Write 'q' to quit from chat", justify="left")
                console.print(f"\n{self.print_message(actual_message)}")
            else:
                console.print(f"{self.print_message(actual_message)}")