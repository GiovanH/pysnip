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
