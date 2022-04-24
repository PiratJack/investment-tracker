import argparse
import logging


def get_log_level():
    # Process commandline arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--debug",
        help=_("Displays detailed information (for debug purpose)"),
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
        default=logging.WARNING,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help=_("Displays additional information (for end users)"),
        action="store_const",
        dest="loglevel",
        const=logging.INFO,
    )
    args = parser.parse_args()
    return args.loglevel
