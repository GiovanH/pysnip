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


def timestamp():
    """Just give a human-readable timestamp.
    Format is %Y-%m-%d %I:%M%p, i.e. "2018-01-02 9:12 PM"

    Returns:
        str: Timestamp
    """
    import datetime

    return datetime.datetime.now().strftime("%Y-%m-%d %I:%M%p")


def bytes_to_string(bytes, units=['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB'], sep="", base=1024):
    """ Returns a human readable string reprentation of bytes."""
    # Adapted from a comment by "Mr. Me" on github.
    if bytes < base:
        return "{:0.2f}{}{}".format(bytes, sep, units[0])
    else:
        return bytes_to_string(bytes / base, units[1:], sep=sep)
