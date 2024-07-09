#  Copyright (C) 2024 RidgeRun, LLC (http://www.ridgerun.com)
#  All Rights Reserved.
#
#  The contents of this software are proprietary and confidential to RidgeRun,
#  LLC.  No part of this program may be photocopied, reproduced or translated
#  into another programming language without prior written consent of
#  RidgeRun, LLC.  The user is free to modify the source code after obtaining
#  a software license from RidgeRun.  All source code changes must be provided
#  back to RidgeRun without any encumbrance.

"""
Search Controller
"""

import logging

from flask import request
from flask_cors import cross_origin
from rrmsutils.models.apiresponse import ApiResponse
from rrmsutils.models.detection.search import Search

from detection.controllers.controller import Controller

logger = logging.getLogger("detection")


class SearchController(Controller):
    """
    Controller for search requests
    """

    def __init__(self, queue):
        self._queue = queue

    def add_rules(self, app):
        """
        Add search update rule at /search uri
        """
        app.add_url_rule('/search', 'update_search',
                         self.update_search, methods=['GET'])

    @cross_origin()
    def update_search(self):
        """
        Validate search request and add it to the queue

        Returns:
            Flask.Response: A Response object with JSON message and a
            code 200 if succesfull or code 400 if failed.
        """

        logger.info(f"new search: {request.args}")
        try:
            search = Search.model_validate(request.args)
        except Exception as e:
            response = ApiResponse(code=1, message=repr(e))
            return self.response(response.model_dump_json(), 400)

        self._queue.put(search)
        return self.response(ApiResponse().model_dump_json(), 200)
