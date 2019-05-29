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
