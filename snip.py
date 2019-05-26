from contextlib import contextmanager
from string import Formatter
# Flow control


def execif(function, args=tuple(), kwargs=dict(), condition=lambda f=None: bool(f)):
    """Shorthand. Executes a function with given args and kwargs if condition coerces to True.
    condition is a function of f, where f is the name of the function itself.

    This allows, amung other things, for function names to be set to None to disable them.

    Args:
        function (TYPE): Description
        args (TYPE, optional): Description
        kwargs (TYPE, optional): Description
        condition (function): Default: bool(function)
        function
        args (list)
        kwargs (dict)
    """
    if condition(function):
        function(*args, **kwargs)


def slow(iterable, delay):
    """A generator that simply throttles another generator or iterable.
    Note that this only throttles the generator, and may become invisible for slow functions.

    Args:
        iterable: Any generator or iterable that supports `for`
        delay (int): Number of seconds between cycles.

    Yields:
        next: type(next(iterable))
    """
    from time import time, sleep
    for next in iterable:
        last = time()
        yield next
        sleep(max(0, (delay - (time() - last))))


# Math

@contextmanager
def timer():
    import time
    start_time = time.time()

    try:
        yield None
    finally:
        time_taken = time.time() - start_time
        print(time_taken)


def bytes_to_string(bytes, units=['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB'], sep="", base=1024):
    """ Returns a human readable string reprentation of bytes."""
    # Adapted from a comment by "Mr. Me" on github.
    if bytes < base:
        return "{:0.2f}{}{}".format(bytes, sep, units[0])
    else:
        return bytes_to_string(bytes / base, units[1:], sep=sep)


# User prompts

# Streams


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
        self.context = "[{n:^{w}.{w}}]".format(w=width, n=vars_['__name__']).format()

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

# String operations


def numSplit(string):
    """Summary

    Args:
        string (TYPE): Description

    Returns:
        TYPE: Description
    """
    import re
    """string.split(), but splits between segments of numbers and letters. 
    Example: numSplit("123abc4d10") == ["123", "abc", "4", "d", "10"]
    
    Args:
        string (str): Input string
    
    Returns:
        List: substrings, split at transitions.
    """
    split = re.compile('(\d+)').split(string)
    return list(filter(lambda x: x != "", split))


# Formatting

def timestamp():
    """Just give a human-readable timestamp.
    Format is %Y-%m-%d %I:%M%p, i.e. "2018-01-02 9:12 PM"

    Returns:
        str: Timestamp
    """
    import datetime

    return datetime.datetime.now().strftime("%Y-%m-%d %I:%M%p")


# Data structures


def chunk(it, size):
    """A generator that yields lists of size `size` containing the results of iterable `it`.

    Args:
        it (iterable): An iterable to split into chunks
        size (int): Max size of chunks

    Yields:
        lists
    """
    from itertools import islice
    iter_it = iter(it)
    for chunk in iter(lambda: tuple(islice(iter_it, size)), ()):
        yield chunk


def flatList(lst):
    """Summary

    Args:
        lst (TYPE): Description

    Returns:
        TYPE: Description
    """
    return [item for sublist in lst for item in sublist]


class Listionary(dict):
    """A special dictionary whose values are exclusively lists. 
    Helper functions included to simplify key: list data structures.
    """

    def __setitem__(self, key, value):
        """Summary

        Args:
            key (TYPE): Description
            value (TYPE): Description
        """
        if type(value) is list:
            super().__setitem__(key, value)
        elif "__len__" in dir(value) and len(value) > 1:
            super().__setitem__(key, [m for m in value])
        else:
            super().__setitem__(key, [value])

    def append(self, key, value, create_needed=True):
        """Append a value to a key's list.

        Args:
            key (TYPE): Description
            value (TYPE): Description
            create_needed (bool, optional): If no list exists, create a new one.
            key
            value

        Returns:
            List: this[key]
        """
        if create_needed:
            self[key] = self.get(key, []) + [value]
        else:
            self[key].append(value)
        return self[key]

    def remove(self, key, value):
        """Remove a value from a key's list. 

        ```self[key].remove(value)
           return self[key]```

        Returns:
            List: this[key]

        Args:
            key (TYPE): Description
            value (TYPE): Description
        """
        self[key].remove(value)
        return self[key]


Dist = Listionary  # :P


class Dummy():
    """Substitute this for other pieces of code for testing purposes.
    Doesn't error out, see example:
    d = Dummy()
    d.fish     # gives another dummy 
    d.get(3)   # gives another dummy
    d[42]      # gives another dummy
    """

    def __getattribute__(self, name):
        return Dummy()

    def __getitem__(self, name):
        return Dummy()

    def __call__(self):
        return Dummy()


class AttrDump():
    """Holds arbitrary attributes. Example:

    a = AttrDump
    a.fish = "fish"
    a.fish
    > "fish"

    "Okay, so obviously THIS one is useless, right?"
    """
    pass


def crawlApi(value, mykey="Root", indent=0):
    if isinstance(value, dict):
        print(" " * indent * 4, mykey, "[{}]".format(type(value)), "...")
        for key in value.keys():
            crawlApi(value[key], key, indent + 1)
    elif isinstance(value, list):
        print(" " * indent * 4, mykey, "[{}]".format(type(value)), "...")
        if len(value) > 0:
            crawlApi(value[0], mykey, indent + 1)
    else:
        print(" " * indent * 4, mykey, "[{}]".format(type(value)), repr(value)[:128])


# File handling

def userProfile(subdir=""):
    import os
    user_profile = os.environ.get("userprofile") or os.path.expanduser("~")
    return os.path.join(user_profile, subdir)


def renameFileOnly(source, destination, clobber=False, quiet=False, preserve_extension=True):
    """Renames file `source` to file `destination`.

    Args:
        source (str): Source path
        destination (str): Destination FILENAME
        clobber (bool, optional): Error instead of overwriting existing files.
        quiet (bool, optional): Print progress to screen

    Returns:
        str: Destination path
    """
    import shutil
    from os import path
    old_dir, old_name = path.split(source)
    new_dir, new_name = path.split(destination)

    assert (new_dir == "" or new_dir == old_dir), "Destination should not be a new path!"

    if preserve_extension:
        old_name_base, old_ext = path.splitext(old_name)
        new_name_base, new_ext = path.splitext(new_name)

        if not (new_ext == "" or new_ext == old_ext):
            print("WARNING: New name should not have a new extension while preserve_extension is True!")

        new_name = new_name_base + new_ext + old_ext

    real_destination = path.join(old_dir, new_name)
    return opFileToFile(shutil.move, source, real_destination, clobber, quiet)


def opFileToDir(op, source, destination, clobber, quiet):
    from os import path
    if not clobber:
        (srcdir, srcfile) = path.split(source)
        new_file_name = path.join(destination, srcfile)
        nfiles = [new_file_name]
    else:
        nfiles = []
    yfiles = [source]
    yfolders = [destination]
    _safetyChecks(yfiles=yfiles, yfolders=yfolders, nfiles=nfiles)
    return _doFileOp(op, source, destination, quiet)


def opFileToFile(op, source, destination, clobber, quiet):
    assert source != destination, "Paths are the same! " + source
    nfiles = [destination] if not clobber else []
    yfiles = [source]
    _safetyChecks(yfiles=yfiles, nfiles=nfiles)
    return _doFileOp(op, source, destination, quiet)


def opDirToParent(op, source, destination, clobber, quiet):
    _safetyChecks(yfolders=[source, destination])
    return _doFileOp(op, source, destination, quiet)


def opDirWithMerge(op, source, destination, clobber, quiet):
    nfolders = [destination] if not clobber else []
    _safetyChecks(yfolders=[source], nfolders=nfolders)
    return _doFileOp(op, source, destination, quiet)


def _safetyChecks(yfiles=[], yfolders=[], nfiles=[], nfolders=[]):
    from os import path
    for file in yfiles:
        if not path.isfile(file):
            raise FileNotFoundError(file)
    for folder in yfolders:
        if not path.isdir(folder):
            raise FileNotFoundError(folder)
    for file in nfiles:
        if path.isfile(file):
            raise FileExistsError(file)
    for folder in nfolders:
        if path.isdir(folder):
            raise FileExistsError(folder)


def _doFileOp(op, source, destination, quiet):
    try:
        result = op(source, destination)
        if not quiet:
            print("{} --> {}".format(source, destination))
        return result
    except Exception as e:
        if not quiet:
            print("{} -x> {}".format(source, destination))
        raise


def copyFileToDir(source, destination, clobber=False, quiet=False):
    """Copies file `source` to folder `destination`.

    Args:
        source (str): Source path
        destination (str): Destination path
        clobber (bool, optional): Error instead of overwriting existing files.
        print (bool, optional): Print progress to screen

    Returns:
        str: Destination path
    """
    import shutil
    return opFileToDir(shutil.copy2, source, destination, clobber, quiet)


def copyFileToFile(source, destination, clobber=False, quiet=False):
    """Copies file `source` to file `destination`.

    Args:
        source (str): Source path
        destination (str): Destination path
        clobber (bool, optional): Error instead of overwriting existing files.
        print (bool, optional): Print progress to screen

    Returns:
        str: Destination path
    """
    import shutil
    return opFileToFile(shutil.copy2, source, destination, clobber, quiet)


def copyDirToParent(source, destination, clobber=False, quiet=False):
    """Copies directory `source` to `destination`. `source` will become a subfolder of `destination`.

    Args:
        source (str): Source path
        destination (str): Destination path
        clobber (bool, optional): Error instead of overwriting existing files.
        print (bool, optional): Print progress to screen

    Returns:
        str: Destination path
    """
    import shutil
    return opDirToParent(shutil.copy2, source, destination, clobber, quiet)


def copyDirWithMerge(source, destination, clobber=False, quiet=False):
    """Copies directory `source` to `destination`. If `destination` is a directory, the two are merged.

    Args:
        source (str): Source path
        destination (str): Destination path
        clobber (bool, optional): Error instead of overwriting existing files.
        print (bool, optional): Print progress to screen

    Returns:
        list: Destination paths
    """
    from distutils.dir_util import copy_tree
    return opDirWithMerge(copy_tree, source, destination, clobber, quiet)


def _copyTreeAndRemove(source, destination):
    """Summary

    Args:
        source (TYPE): Description
        destination (TYPE): Description
    """
    from distutils.dir_util import copy_tree
    import os
    result = copy_tree(source, destination)
    os.unlink(source)
    return result


def moveFileToDir(source, destination, clobber=False, quiet=False):
    """Moves file `source` to folder `destination`.

    Args:
        source (str): Source path
        destination (str): Destination path
        clobber (bool, optional): Error instead of overwriting existing files.
        quiet (bool, optional): Print progress to screen

    Returns:
        str: Destination path
    """
    import shutil
    return opFileToDir(shutil.move, source, destination, clobber, quiet)


def moveFileToFile(source, destination, clobber=False, quiet=False):
    """Moves file `source` to file `destination`.

    Args:
        source (str): Source path
        destination (str): Destination path
        clobber (bool, optional): Error instead of overwriting existing files.
        quiet (bool, optional): Print progress to screen

    Returns:
        str: Destination path
    """
    import shutil
    return opFileToFile(shutil.move, source, destination, clobber, quiet)


def moveDirToParent(source, destination, clobber=False, quiet=False):
    """Moves directory `source` to `destination`. `source` will become a subfolder of `destination`.

    Args:
        source (str): Source path
        destination (str): Destination path
        clobber (bool, optional): Error instead of overwriting existing files.
        quiet (bool, optional): Print progress to screen

    Returns:
        str: Destination path
    """
    import shutil
    return opDirToParent(shutil.move, source, destination, clobber, quiet)


def moveDirWithMerge(source, destination, clobber=False, quiet=False):
    """Moves directory `source` to `destination`. If `destination` is a directory, the two are merged.

    Args:
        source (str): Source path
        destination (str): Destination path
        clobber (bool, optional): Error instead of overwriting existing files.
        quiet (bool, optional): Print progress to screen

    Returns:
        list: Destination paths
    """
    return opDirWithMerge(_copyTreeAndRemove, source, destination, clobber, quiet)


# Hashing


def md5(path):
    """Returns the md5 hash of the file at (str) path.

    Args:
        path (str): Path to file

    Returns:
        str: Hex digest of md5 hash
    """
    from hashlib import md5
    hasher = md5()
    with open(path, 'rb') as afile:
        buf = afile.read()
        hasher.update(buf)
    return hasher.hexdigest()


def CRC32(filename):
    """Returns the CRC32 "hash" of the file at (str) path.

    Args:
        filename (str): Path to file

    Returns:
        str: Formated CRC32, as {:08X} formatted.

    """
    from binascii import crc32
    buf = open(filename, 'rb').read()
    buf = (crc32(buf) & 0xFFFFFFFF)
    return "{:08X}".format(buf)
