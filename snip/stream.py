# Streams

from contextlib import contextmanager
from string import Formatter
from sys import argv
import shutil
import os

import logging
import logging.handlers


def timestamp():
    """Just give a human-readable timestamp.
    Format is %Y-%m-%d %I:%M%p, i.e. "2018-01-02 9:12 PM"

    Returns:
        str: Timestamp
    """
    import datetime

    return datetime.datetime.now().strftime("%Y-%m-%d %I:%M%p")


def makeLogHandler(base, level, format_string):
    h = base
    h.setLevel(level)
    h.setFormatter(logging.Formatter(format_string, "%Y-%m-%d %H:%M:%S"))
    return h


active_log_handlers = {}


def TriadLogger(__name, stream=True, file=True, debug=True, retries=0):
    """Logger that outputs to stdout, a logfile, and a debug logfile with extra verbosity.
    Use with logger = TriadLogger(__name__)

    Also, tries to share file handlers, for multiple loggers running in the same program.

    Args:
        __name (TYPE): Description
        stream (bool, optional): Whether to use stdout
        file (bool, optional): Whether to use a logfile
        debug (bool, optional): Whether to use a debug logfile

    Returns:
        logger
    """
    global active_log_handlers

    def makeLogHandler(base, level, format_string):
        h = base
        h.setLevel(level)
        h.setFormatter(logging.Formatter(format_string, "%Y-%m-%d %H:%M:%S"))
        return h

    logger = logging.getLogger(__name)
    logger.setLevel(logging.DEBUG)

    # depending on execution context, may not have an arg0?
    progname = argv[0].replace('.py', '') or __name

    # Handle multiple simultaneous processes
    if retries > 0:
        if retries > 20:
            raise Exception("Cannot open logfile! Too many instances open?")
        progname = f"{progname}{retries}"

    filepath_normal = f"{progname}_latest.log"
    filepath_debug = f"{progname}_latest_debug.log"

    try:

        if file:
            if not active_log_handlers.get("file"):
                if os.path.isfile(filepath_normal):
                    shutil.move(filepath_normal, filepath_normal + ".bak")
                active_log_handlers["file"] = makeLogHandler(
                    logging.handlers.RotatingFileHandler(filepath_normal, mode="w"),
                    logging.INFO,
                    '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
                )
            logger.addHandler(active_log_handlers["file"])

        if debug:
            if not active_log_handlers.get("debug"):
                if os.path.isfile(filepath_debug):
                    shutil.move(filepath_debug, filepath_debug + ".bak")
                active_log_handlers["debug"] = makeLogHandler(
                    logging.handlers.RotatingFileHandler(filepath_debug, mode="w", encoding="utf-8"),
                    logging.DEBUG,
                    '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
                )
            logger.addHandler(active_log_handlers["debug"])

        if stream:
            if not active_log_handlers.get("stream"):
                active_log_handlers["stream"] = makeLogHandler(
                    logging.StreamHandler(),
                    logging.INFO,
                    '[%(name)s] %(levelname)s: %(message)s'
                )
            logger.addHandler(active_log_handlers["stream"])

        return logger

    except PermissionError as e:
        print(f"'{filepath_normal}' is busy(?), incrementing")
        print(e)
        return TriadLogger(__name, stream=stream, file=file, debug=debug, retries=(retries + 1))


class ContextPrinter():

    """Similar to a logger. Wraps print with the statements file name and context.
    """

    def __init__(self, vars_, width=10, timestamp=True):
        """Context

        Args:
            vars_ (vars()): Initialize with the vars() call
            width (int, optional): Width of text box
            timestamp (bool, optional): Whether to display a time stamp or not

        """

        from builtins import print as bprint
        self.print = bprint
        self.timestamp = timestamp
        self.context = "[{n:^{w}.{w}} {h}]".format(
            w=width,
            n=vars_['__name__'],
            h=str(id(vars_))[-7:-1]
        )

    def __call__(self, *args, **kwargs):
        if len(args) == 0:
            args = ["-" * 8]
        if self.timestamp:
            self.print("[{}]".format(timestamp()), end="\t")
        self.print(self.context, end="\t")
        self.print(*args, **kwargs)


class DefaultFormatter(Formatter):

    """Summary

    Attributes:
        defaults (TYPE): Description
    """

    def __init__(self, **kwargs):
        """Summary

        Args:
            **kwargs: Description
        """
        Formatter.__init__(self)
        self.defaults = kwargs

    def get_value(self, key, args, kwargs):
        """Summary

        Args:
            key (TYPE): Description
            args (TYPE): Description
            kwargs (TYPE): Description

        Returns:
            TYPE: Description
        """
        if isinstance(key, str):
            passsedValue = kwargs.get(key)
            if passsedValue is not None:
                return passsedValue
            return self.defaults[key]
        else:
            super().get_value(key, args, kwargs)


class Tee(object):
    def __init__(self, stream_a, stream_b):
        self.stream_a = stream_a
        self.stream_b = stream_b

    def __del__(self):
        self.close()

    def close(self):
        pass
        # self.stream_a.close()
        # self.stream_b.close()

    def write(self, data):
        self.stream_a.write(data)
        self.stream_b.write(data)

    def flush(self):
        self.stream_a.flush()
        self.stream_b.flush()

    def __enter__(self):
        pass

    def __exit__(self, _type, _value, _traceback):
        pass


stream_tee = Tee


@contextmanager
def std_redirected(outfile, errfile=None, tee=False):
    """Summary

    Args:
        outfile (TYPE): Description
        errfile (None, optional): Description

    Yields:
        TYPE: Description
    """
    import sys  # Must import basename for naming to bind globally
    if errfile is None:
        errfile = outfile

    # Save file handle
    _stdout = sys.stdout
    _stderr = sys.stderr

    sys.stdout = open(outfile, 'w')
    sys.stderr = open(errfile, 'w') if outfile != errfile else sys.stdout

    if tee:
        sys.stdout = Tee(sys.stdout, _stdout)
        sys.stderr = Tee(sys.stderr, _stderr)

    try:
        yield None
    finally:
        sys.stdout.close()
        sys.stderr.close()  # Safe to use even if stdout == stderr
        sys.stdout = _stdout
        sys.stderr = _stderr
