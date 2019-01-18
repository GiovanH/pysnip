"""Summary
"""
# Math


# def wraparound(index, max):
#     """
#     Returns:
#         index   if 0 <= index < max
#         max - 1 if index < 0
#         0       if indeex >= max
#         Max is, pythonically, exclusive, so len(x) can be an argument
    
#     Args:
#         index (TYPE): Description
#         max (TYPE): Description
#     """
#     if index < 0:
#         index = max - 1
#     if index >= max:
#         index = 0
#     return index

#     # TODO: I think this is just modulo?


# String operations


def numSplit(string):
    """string.split(), but splits between segments of numbers and letters. 
    Example: numSplit("123abc4d10") == ["123", "abc", "4", "d", "10"]
    
    Args:
        string (str): Input string
    
    Returns:
        List: substrings, split at transitions.
    """
    split = re.compile('(\d+)').split(string)
    return list(filter(lambda x: x != "", split))


# Data structures


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
            key
            value
            create_needed (bool, optional): If no list exists, create a new one.
        
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


# File handling



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
        path (str): Path to file
    
    Returns:
        str: Formated CRC32, as {:08X} formatted.
    """
    from binascii import crc32
    buf = open(filename, 'rb').read()
    buf = (crc32(buf) & 0xFFFFFFFF)
    return "{:08X}".format(buf)
