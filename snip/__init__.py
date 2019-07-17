"""
Snip
~~~~~~

Snip: A library of generic helper functions for utility programs.
"""

from . import data, filesystem, flow, hash, stream, string 
from . import jfileutil, loom
from . import prompt
from . import nest

# import importlib

# modulesNotImported = []
# modulesNotFound = []

# for module in ["image", "audio", "tkit", "pwidgets", "net"]:
#     try:
#         importlib.import_module("." + module, __name__)
#     except ModuleNotFoundError as e:
#         modulesNotImported.append(module)
#         modulesNotFound.append(e.name)

# if modulesNotFound:
#     print(
#         f"WARNING: Oprional '{__name__}' submodules {modulesNotImported} not imported, "
#         f"missing dependencies: {modulesNotFound}"
#     )
