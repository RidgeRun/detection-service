#  Copyright (C) 2024 RidgeRun, LLC (http://www.ridgerun.com)
#  All Rights Reserved.
#
#  The contents of this software are proprietary and confidential to RidgeRun,
#  LLC.  No part of this program may be photocopied, reproduced or translated
#  into another programming language without prior written consent of
#  RidgeRun, LLC.  The user is free to modify the source code after obtaining
#  a software license from RidgeRun.  All source code changes must be provided
#  back to RidgeRun without any encumbrance.

"""Server entry point
"""

import argparse
import logging
from queue import Queue
from threading import Thread

from detection.controllers.searchcontroller import SearchController
from detection.controllers.sourcecontroller import SourceController
from detection.detection import Detection
from detection.server import Server

logger = logging.getLogger("detection")


def list_of_strings(arg):
    """ Define a custom argument type for a list of strings """
    return arg.split(',')


def list_of_floats(arg):
    """ Define a custom argument type for a list of floats """
    return list(map(float, arg.split(',')))


def parse_args():
    """ Parse arguments """
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5030,
                        help="Port for server")
    parser.add_argument("--host", type=str, default='127.0.0.1',
                        help="Server ip address")
    parser.add_argument("--objects", type=list_of_strings, default=None,
                        help="List of objects to detect, example: 'a person,a box,a ball'")
    parser.add_argument("--thresholds", type=list_of_floats, default=None,
                        help="List of thresholds corresponding to the objects, example: 0.1,0.2,0.65")
    parser.add_argument("--vertical-slices", type=int, default=1,
                        help="Divide the image in given amount of vertical slices to detect small objects")
    parser.add_argument("--horizontal-slices", type=int, default=1,
                        help="Divide the image in given amount of horizontal slices to detect small objects")

    args = parser.parse_args()

    return args


def main():
    """
    Main application
    """
    args = parse_args()
    logging.basicConfig(level=logging.INFO)

    controllers = []
    search_queue = Queue()
    source_queue = Queue()
    controllers.append(SearchController(search_queue))
    controllers.append(SourceController(source_queue))

    logger.info("Launch flask server")
    server = Server(controllers, host=args.host, port=args.port)
    server_thread = Thread(target=server.start, daemon=True)
    server_thread.start()

    detection = Detection(search_queue, source_queue, objects=args.objects,
                          thresholds=args.thresholds, vertical_slices=args.vertical_slices,
                          horizontal_slices=args.horizontal_slices)
    detection.loop()


if __name__ == "__main__":
    main()
