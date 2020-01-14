# Streams

from contextlib import contextmanager
from string import Formatter
from sys import argv

from .strings import timestamp

import logging


def makeLogHandler(base, level, format_string):
    h = base
    h.setLevel(level)  
    h.setFormatter(logging.Formatter(format_string, "%Y-%m-%d %H:%M:%S"))
    return h


active_log_handlers = {}


def TriadLogger(__name, stream=True, file=True, debug=True):
    global active_log_handlers
    
    logger = logging.getLogger(__name)
    logger.setLevel(logging.DEBUG)

    if stream:
        if not active_log_handlers.get("stream"):
            active_log_handlers["stream"] = makeLogHandler(logging.StreamHandler(), logging.INFO, '[%(name)s] %(levelname)s: %(message)s')
        logger.addHandler(active_log_handlers["stream"])
    
    if file:
        if not active_log_handlers.get("file"):
            active_log_handlers["file"] = makeLogHandler(logging.FileHandler(f"{argv[0]}_latest.log", mode="w"), logging.INFO, '%(asctime)s [%(name)s] %(levelname)s: %(message)s')
        logger.addHandler(active_log_handlers["file"])

    if debug:
        if not active_log_handlers.get("file_debug"):
            active_log_handlers["file_debug"] = makeLogHandler(logging.FileHandler(f"{argv[0]}_latest_debug.log", mode="w", encoding="utf-8"), logging.DEBUG, '%(asctime)s [%(name)s] %(levelname)s: %(message)s')
        logger.addHandler(active_log_handlers["file_debug"])

    return logger


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

