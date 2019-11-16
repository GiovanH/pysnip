# Streams

from contextlib import contextmanager
from string import Formatter

from .strings import timestamp


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

