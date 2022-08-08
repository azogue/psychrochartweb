# -*- coding: utf-8 -*-
if __name__ == "__main__":
    import logging
    import sys

    import uvloop
    from aiohttp import web

    from .app import create_app
    from .config import get_config

    # Install uvloop
    uvloop.install()

    # Create application and get its config
    app = create_app(name="psychrochartweb")

    # Now run the application
    app_config = get_config(app)
    logging.basicConfig(
        level=app_config.LOGGING_LEVEL,
        format=(
            "%(asctime)s.%(msecs)03d %(levelname)s: "
            "(%(filename)s:%(lineno)s): %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    web.run_app(app, host=app_config.HOST, port=app_config.PORT)

    sys.exit(0)
