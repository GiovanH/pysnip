"""Summary
"""
from snip import jfileutil as ju
from json.decoder import JSONDecodeError


class Nest():

    """Wrapper for a series of nested dictionaries
    
    Attributes:
        dictionary (dict): The dictionary this wraps
        identifier (str): The name of the JSON file backing the dict
    """
    
    def __init__(self, default=None):
        """Args:
            identifier (str): The name of the JSON file backing the dict
            default (dict, optional): Use this dictionary if file errors
            default (dict, optional): Load this dictionary and replace the file
        """
        super(Nest, self).__init__()
        if default is None:
            self.dictionary = dict()
        else:
            self.dictionary = default

    def keys(self, root=None):
        if not root:
            root = self.dictionary
        return self.dictionary.keys()

    def get(self, keypath="", default=None, root=None):
        """Summary
        
        Args:
            key (str, optional): Key. Format is `[.]{dict.}key` Returns value.
            root (None, optional): Description
        
        Returns:
            object: Value
        
        Raises:
            KeyError: No path exists
            ValueError: No value exists
        """
        if not root:
            root = self.dictionary
        keystack = key.split(".")
        while len(keystack) > 0:
            nextkey = keystack.pop(0)
            if nextkey == "" or nextkey == "root":
                root = root
            else:
                if root.get(nextkey) is None:
                    raise KeyError("No path: " + nextkey)
                root = root[nextkey]
        if root is None:  # Boolean miss
            raise ValueError("none: " + nextkey)
        return root

    def set(self, key, value):
        """Set a key to a value.
        
        Args:
            key (str): Keypath
        """
        print(key, value)
        keystack = key.split(".")
        root = self.dictionary
        while len(keystack) > 1:
            nextkey = keystack.pop(0)
            if nextkey == "" or nextkey == "root":
                root = root
            else:
                if not root.get(nextkey):
                    root[nextkey] = dict()
                root = root[nextkey]
        nextkey = keystack.pop(0)
        root[nextkey] = value

    def flatten(self, key="", root=None, trees=False, leaves=True):
        """Returns a flat list 
        
        Args:
            key (str, optional): Starting key. Defaults to root.
            root (dict, optional): Recursion
        
        Yields:
            list: List of strings
        """
        if not root:
            root = self.dictionary
        for subkey in root.keys():
            if key == "":
                nextkey = subkey
            else:
                if leaves:
                    yield(key, None)
                nextkey = key + "." + subkey
            if isinstance(root[subkey], dict):
                for t in self.flatten(key=nextkey, root=root[subkey], trees=trees, leaves=leaves):
                    if not (not trees and t[1] is None):
                        yield t
            else:
                yield(nextkey, root[subkey])


class FsNest(Nest):

    def __init__(self, identifier, default=None):
        """Args:
            identifier (str): The name of the JSON file backing the dict
            default (dict, optional): Use this dictionary if file errors
            load (dict, optional): Load this dictionary and replace the file
        """
        super(Nest, self).__init__()
        self.identifier = identifier

    def reload(self):
        """Load json from file
        """
        self.dictionary = ju.load(self.identifier)

    def rename(self, newname):
        """Rename JSON file
        
        Args:
            newname (str): New file identifier
        """
        self.identifier = newname
        self.flush()

    def save(self):
        """Save data to file
        """
        ju.save(self.dictionary, self.identifier)


def test():
    """Run test cases
    """
    nest1 = Nest()
    nest1.set("nestlvl1", dict())
    nest1.set("nestlvl1.nestlvl2", [3])
    nest1.set("nestlvl1b.nestlvl2", 3)
    assert nest1.get("nestlvl1b.nestlvl2") == 3
    # nest2 = Nest("Test2", load={})


if __name__ == "__main__":
    test()
