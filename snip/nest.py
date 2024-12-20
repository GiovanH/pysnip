"""Summary
"""
from . import jfileutil as ju
# from json.decoder import JSONDecodeError

from snip.stream import TriadLogger
logger = TriadLogger(__name__)

class Nest():

    """Wrapper for a series of nested dictionaries

    Attributes:
        dictionary (dict): The dictionary this wraps
        identifier (str): The name of the JSON file backing the dict
    """

    def __init__(self, default={}):
        """Args:
            identifier (str): The name of the JSON file backing the dict
            default (dict, optional): Use this dictionary if file errors
            default (dict, optional): Load this dictionary and replace the file
        """
        super().__init__()
        # logger.info("Setting default dictionary")
        # logger.debug(default)
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

        keystack = keypath.split(".")
        while len(keystack) > 0:
            nextkey = keystack.pop(0)

            # If there is no next key, we stop.
            if nextkey == "" or nextkey == "root":
                break

            # If we can't go to the next key, handle it.
            if root.get(nextkey) is None:
                if default:
                    return default
                else:
                    raise KeyError("No path:", keypath, nextkey)

            # Go to the next key
            root = root[nextkey]

        return root

    def set(self, keypath, value, makepath=True):
        """Set a key to a value.

        Args:
            key (str): Keypath
        """
        keystack = keypath.split(".")
        root = self.dictionary
        while len(keystack) > 1:
            nextkey = keystack.pop(0)

            # If there is no next key, we stop.
            if nextkey == "" or nextkey == "root":
                break

            if root.get(nextkey) is None:
                if makepath:
                    root[nextkey] = dict()
                else:
                    raise KeyError("No path: ", keypath, nextkey)

            # Traverse
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

    def __init__(self, identifier, **kwargs):
        """Args:
            identifier (str): The name of the JSON file backing the dict
            default (dict, optional): Use this dictionary if file errors
            load (dict, optional): Load this dictionary and replace the file
        """
        super().__init__(**kwargs)
        self.identifier = identifier
        self.reload()

    def reload(self):
        """Load json from file, if identifier is set.
        """
        if (self.identifier):
            try:
                self.dictionary = ju.load(self.identifier)
            except:
                logger.warning(f"File for FsNest {self.identifier} does not exist, not loading.")

    def rename(self, newname):
        """Rename JSON file

        Args:
            newname (str): New file identifier
        """
        self.identifier = newname
        self.save()

    def save(self):
        """Save data to file, if identifier is set.
        """
        if (self.identifier):
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
