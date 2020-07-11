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
    yield from iter(lambda: tuple(islice(iter_it, size)), ())


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


def writeJsonToCsv(data, filepath, ext=True):

    def escape(obj):
        if isinstance(obj, str):
            obj = obj.replace("\n", "\\n").replace("\"", "\"\"")
        if isinstance(obj, list):
            obj = "; ".join(map(repr, obj))
            return escape(obj)
        return '"{}"'.format(obj)

    from . import nest

    flat_entries = [dict(nest.Nest(entry).flatten()) for entry in data]
    columns = sorted(set(flatList(entry.keys() for entry in flat_entries)))

    if ext:
        filepath = filepath + ".csv"

    with open(filepath, "w", encoding="utf-8") as fp:
        fp.write(",".join('"{}"'.format(column) for column in columns) + "\n")
        fp.writelines(
            ",".join(
                escape(row.get(key)) for key in columns
            ) + "\n" for row in flat_entries
        )
