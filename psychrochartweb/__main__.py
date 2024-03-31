import logging

from uvicorn import Config, Server

from psychrochartweb.app import create_app
from psychrochartweb.config import Settings


def main_app() -> None:
    """Entry point for Uvicorn app."""
    app_settings = Settings()
    logging.basicConfig(
        level=app_settings.app_log_level,
        handlers=[logging.StreamHandler()],
        format="%(asctime)s.%(msecs)03d %(levelname)s: "
        "(%(filename)s:%(lineno)s): %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    app = create_app(app_settings)
    server = Server(
        Config(
            app=app,
            host="0.0.0.0",
            port=app_settings.app_port,
            loop="uvloop",
        ),
    )
    server.run()


if __name__ == "__main__":
    main_app()
