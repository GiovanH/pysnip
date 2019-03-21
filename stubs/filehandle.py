def copyFileToDir(source, destination, clobber=False, print=False):
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
    return opFileToDir(shutil.copy2, source, destination, clobber, print)


def copyFileToFile(source, destination, clobber=False, print=False):
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
    return opFileToFile(shutil.copy2, source, destination, clobber, print)


def copyDirToParent(source, destination, clobber=False, print=False):
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
    return opDirToParent(shutil.copy2, source, destination, clobber, print)


def copyDirWithMerge(source, destination, clobber=False, print=False):
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
    return opDirWithMerge(copy_tree, source, destination, clobber, print)


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


def moveFileToDir(source, destination, clobber=False, verbose=True):
    """Moves file `source` to folder `destination`.
    
    Args:
        source (str): Source path
        destination (str): Destination path
        clobber (bool, optional): Error instead of overwriting existing files.
        verbose (bool, optional): Print progress to screen
    
    Returns:
        str: Destination path
    """
    import shutil
    return opFileToDir(shutil.move, source, destination, clobber, verbose)


def moveFileToFile(source, destination, clobber=False, verbose=True):
    """Moves file `source` to file `destination`.
    
    Args:
        source (str): Source path
        destination (str): Destination path
        clobber (bool, optional): Error instead of overwriting existing files.
        verbose (bool, optional): Print progress to screen
    
    Returns:
        str: Destination path
    """
    import shutil
    return opFileToFile(shutil.move, source, destination, clobber, verbose)


def moveDirToParent(source, destination, clobber=False, verbose=True):
    """Moves directory `source` to `destination`. `source` will become a subfolder of `destination`.
    
    Args:
        source (str): Source path
        destination (str): Destination path
        clobber (bool, optional): Error instead of overwriting existing files.
        verbose (bool, optional): Print progress to screen
    
    Returns:
        str: Destination path
    """
    import shutil
    return opDirToParent(shutil.move, source, destination, clobber, verbose)


def moveDirWithMerge(source, destination, clobber=False, verbose=True):
    """Moves directory `source` to `destination`. If `destination` is a directory, the two are merged.
    
    Args:
        source (str): Source path
        destination (str): Destination path
        clobber (bool, optional): Error instead of overwriting existing files.
        verbose (bool, optional): Print progress to screen
    
    Returns:
        list: Destination paths
    """
    return opDirWithMerge(_copyTreeAndRemove, source, destination, clobber, verbose)