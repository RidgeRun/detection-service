#  Copyright (C) 2024 RidgeRun, LLC (http://www.ridgerun.com)
#  All Rights Reserved.
#
#  The contents of this software are proprietary and confidential to RidgeRun,
#  LLC.  No part of this program may be photocopied, reproduced or translated
#  into another programming language without prior written consent of
#  RidgeRun, LLC.  The user is free to modify the source code after obtaining
#  a software license from RidgeRun.  All source code changes must be provided
#  back to RidgeRun without any encumbrance.

"""Base HTTP server using Flask.
"""

from flask import Flask


class Server:
    """
    Flask server
    """

    def __init__(self, controllers: list, host: str = '127.0.0.1', port: int = 8550):
        """Create an HTTP server using Flask

        Args:
            controllers (list): A list of controllers
            host (str, optional): Server address. Defaults to 127.0.0.1.
            port (int, optional): Server port. Defaults to 8550.
        """
        self._port = port
        self._host = host
        self._app = Flask(__name__)

        # Add rules
        for controller in controllers:
            controller.add_rules(self._app)

    def start(self):
        """
        Run the server with given port.
        """
        self._app.run(use_reloader=False, host=self._host, port=self._port)
