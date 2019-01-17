"""Utility functions for storing and loading json data.

Attributes:
    basepath (str): Basepath for object files.
    basepath_json (str): Basepath for json files.
    basepath_pick (str): Basepath for pickle files.
"""
import json
# import pickle
from os import makedirs, path
import shutil   

# Version 1.5

basepath_json = "./jobj/" 
basepath_pick = "./obj/" 


# def load(filename):
#     """Args:
#         filename (string): Identifier for object
    
#     Returns:
#         Object
#     """
#     return json_load(filename)


# def save(object, filename):
#     """Args:
#         object (object): Object to store
#         filename (string): Identifier for object
#     """
#     return json_save(object, filename)
def get_json_path(basepath, filename):
    return path.relpath(path.join(basepath, filename + ".json"))


def json_load(filename, basepath=basepath_json, default=None):
    """Args:
        filename (string): Identifier for object
    
    Returns:
        Object
    """
    try:
        with open(get_json_path(basepath, filename), 'r') as file:
            return json.load(file)
    except Exception as e:
        if default is not None:
            return default
        else:
            raise


def json_save(object, filepath, basepath=basepath_json):
    """Args:
        object (object)
        filename (string): Identifier for object
    """
    filepath = get_json_path(basepath, filepath)
    (fdirs, fname) = path.split(filepath)
    makedirs(fdirs, exist_ok=True)
    with open(filepath, 'w') as file:
        json.dump(object, file, indent=4)


load = json_load
save = json_save


class Handler():

    def __init__(self, name, default=None, basepath=basepath_json, readonly=False):
        self.name = name
        self.default = default
        self.readonly = readonly
        self.basepath = basepath
        self.obj = None

    def __enter__(self):
        self.obj = load(self.name, basepath=self.basepath, default=self.default)
        return self.obj

    def __exit__(self, type, value, traceback):
        if self.readonly:
            save(self.obj, self.name, basepath=self.basepath)

    def flush(self):
        if self.readonly:
            raise NotImplemented("Cannot save if readonly is True.")
        else:
            save(self.obj, self.name, basepath=self.basepath)


class RotatingHandler(Handler):
    def __init__(self, name, default=None, basepath=basepath_json, readonly=False):
        super(RotatingHandler, self).__init__(
            name,
            default=default, basepath=basepath, readonly=readonly
        )

    def __enter__(self):
        try:
            return super(RotatingHandler, self).__enter__()
        except json.JSONDecodeError as e:
            print("Warning: data file '{}' corrupted. ".format(self.name))
            print("Deleting corrupted data")
            shutil.os.remove(self.name)
            print("Restoring backup")
            shutil.copy2(
                get_json_path(self.basepath, self.name) + ".bak",
                get_json_path(self.basepath, self.name)
            ) 
            return super(RotatingHandler, self).__enter__()

    def __exit__(self, type, value, traceback):
        super(RotatingHandler, self).__exit__(type, value, traceback)
        shutil.copy2(
            get_json_path(self.basepath, self.name),
            get_json_path(self.basepath, self.name) + ".bak"
        ) 