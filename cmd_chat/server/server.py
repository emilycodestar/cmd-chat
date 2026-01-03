from typing import Optional
from .factory import create_app


def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    password: Optional[str] = None,
    workers: int = 1,
) -> None:
    app = create_app(password=password or "")

    app.run(
        host=host,
        port=port,
        single_process=True,
        debug=False,
        access_log=True,
    )
