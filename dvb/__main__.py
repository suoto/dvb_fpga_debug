#!/usr/bin/env python3

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=wrong-import-position

import argparse
import logging
import sys

from dvb.dvb_encoder import DvbEncoder  # type: ignore
from dvb.logger import setupLogging


def _parseArgs():
    "Parse command line arguments"
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verbose",
        "-v",
        action="append_const",
        const=1,
        help="Increases verbosity. Passing multiple times progressively increases verbosity",
    )
    parser.add_argument(
        "--monitor",
        #  "-m",
        action="store",
        help="Address to listen to when publishing stats",
    )
    parser.add_argument(
        "--print-constellation-map",
        "-m",
        action="store_true",
    )

    args = parser.parse_args()

    level = logging.WARNING

    if args.verbose:
        if len(args.verbose) == 1:
            level = logging.INFO
        elif len(args.verbose) == 2:
            level = logging.DEBUG
        elif len(args.verbose) > 2:
            level = 4

    setupLogging(sys.stdout, level, True)
    globals()["_logger"] = logging.getLogger(__name__)

    return args


def dvbStatus():
    args = _parseArgs()
    encoder = DvbEncoder(0x0_0000, 16 * 1024)
    if args.monitor:
        import bottle  # type: ignore

        encoder = DvbEncoder(0, 16 * 1024)

        @bottle.route("/read/status")
        def index():
            result = encoder.getStatus()
            return result

        host = args.monitor.split(":")
        port = 60001
        if isinstance(host, list):
            host, port = host
        bottle.run(host=host, port=port)
    else:
        encoder.printStatus(args.print_constellation_map)
