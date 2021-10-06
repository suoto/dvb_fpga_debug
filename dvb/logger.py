import logging
import os
import os.path as p
import sys
from threading import Lock


def setupLogging(stream, level, color=True):  # pragma: no cover
    "Setup logging according to the command line parameters"
    if isinstance(stream, str):

        class Stream(object):
            """
            File subclass that allows RainbowLoggingHandler to write
            with colors
            """

            _lock = Lock()
            _color = color

            def __init__(self, *args, **kwargs):
                self._fd = open(*args, **kwargs)

            def isatty(self):
                """
                Tells if this stream accepts control chars
                """
                return self._color

            def write(self, text):
                """
                Writes to the stream
                """
                with self._lock:
                    self._fd.write(text.encode("utf-8", errors="replace"))

        _stream = Stream(stream, "ab", buffering=0)
    else:
        _stream = stream

    try:
        from rainbow_logging_handler import RainbowLoggingHandler

        handler = RainbowLoggingHandler(
            _stream,
            #  Customizing each column's color
            # pylint: disable=bad-whitespace
            color_asctime=("white", "black"),
            color_name=("white", "black"),
            color_funcName=("green", "black"),
            color_lineno=("white", "black"),
            color_pathname=("black", "red"),
            color_module=("yellow", None),
            color_message_debug=("cyan", None),
            color_message_info=(None, None),
            color_message_warning=("yellow", None),
            color_message_error=("red", None),
            color_message_critical=("bold white", "red"),
        )
        # pylint: enable=bad-whitespace
    except ImportError:  # pragma: no cover
        handler = logging.StreamHandler(_stream)
        handler.formatter = logging.Formatter(
            "%(levelname)-7s | %(asctime)s | "
            + "%(name)s @ %(funcName)s():%(lineno)d "
            + "|\t%(message)s",
            datefmt="%H:%M:%S",
        )

    logging.root.addHandler(handler)
    logging.root.setLevel(level)


#  setupLogging(sys.stdout, logging.DEBUG, True)
#  _logger = logging.getLogger(__name__)
#  _logger.info("Path: %s", sys.path)
#  _logger.info("Python version is %s", sys.version.replace("\n", ", "))
