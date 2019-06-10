# Streams

from contextlib import contextmanager
from string import Formatter

from .string import timestamp


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
            h=hash(vars_.get('__self__', 0)) % 1000
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


@contextmanager
def std_redirected(filename, errname=None, tee=False):
    """Summary

    Args:
        filename (TYPE): Description
        errname (None, optional): Description

    Yields:
        TYPE: Description
    """
    from os import makedirs
    from os.path import split as psplit
    import sys  # Must import basename for naming to bind globally
    if errname is None:
        errname = filename
    makedirs(psplit(filename)[0], exist_ok=True)
    makedirs(psplit(errname)[0], exist_ok=True)

    # Save file handle
    _stdout = sys.stdout
    _stderr = sys.stderr

    sys.stdout = open(filename, 'w')
    sys.stderr = open(errname, 'w') if filename != errname else sys.stdout

    if tee:
        sys.stdout = stream_tee(sys.stdout, _stdout)
        sys.stderr = stream_tee(sys.stderr, _stderr)

    try:
        yield None
    finally:
        sys.stdout.close()
        sys.stderr.close()  # Safe to use even if stdout == stderr
        sys.stdout = _stdout
        sys.stderr = _stderr


class stream_tee(object):
    # Based on https://gist.github.com/327585 by Anand Kunal
    def __init__(self, stream1, stream2):
        self.stream1 = stream1
        self.stream2 = stream2
        self.__missing_method_name = None  # Hack!

    def __getattribute__(self, name):
        return object.__getattribute__(self, name)

    def __getattr__(self, name):
        self.__missing_method_name = name  # Could also be a property
        return getattr(self, '__methodmissing__')

    def __methodmissing__(self, *args, **kwargs):
            # Emit method call to the log copy
        callable2 = getattr(self.stream2, self.__missing_method_name)
        callable2(*args, **kwargs)

        # Emit method call to stdout (stream 1)
        callable1 = getattr(self.stream1, self.__missing_method_name)
        return callable1(*args, **kwargs)
