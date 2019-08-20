# Hashing


def md5file(path):
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

def md5data(data):
    """Returns the md5 hash of some data

    Args:
        data: Binary data

    Returns:
        str: Hex digest of md5 hash
    """
    from hashlib import md5
    hasher = md5()
    hasher.update(data)
    return hasher.hexdigest()


def CRC32file(filename):
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


def CRC32data(data):
    """Returns the CRC32 "hash" of some data

    Args:
        data: Binary data

    Returns:
        str: Formated CRC32, as {:08X} formatted.

    """
    from binascii import crc32
    buf = (crc32(data) & 0xFFFFFFFF)
    return "{:08X}".format(buf)
