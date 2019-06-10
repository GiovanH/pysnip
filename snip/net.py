"""Networking functions
"""

from urllib.parse import urljoin
import requests
import bs4
from .filesystem import easySlug


def getSoup(url, prev_url=None):
    """Get a BeautifulSoup object from a URL
    
    Args:
        url (str): Remote URL
        prev_url (str, optional): Previous url, for relative resolution
    
    Returns:
        soup: Beautiful Soup
    """
    url = urljoin(prev_url, url)
    resp = requests.get(url)
    resp.raise_for_status()
    soup = bs4.BeautifulSoup(resp.text, features="html.parser")
    return soup


def getStream(url, prev_url=None):
    """Extremely light, dumb helper to get a stream from a url
    
    Args:
        url (str): Remote URL
        prev_url (str, optional): Previous url, for relative resolution
    
    Returns:
        Requests stream
    """
    url = urljoin(prev_url, url)
    stream = requests.get(url, stream=True)
    return stream


def saveStreamAs(stream, dest_path):
    """Save a URL to a path as file
    
    Args:
        stream (stream): Stream
        dest_path (str): Local path

    Returns:
        bool: Success
    """
    from os import path, stat
    from math import inf

    stream_length = stream.headers.get("Content-Length", inf)
    if path.isfile(dest_path) and stream_length == stat(dest_path).st_size:
        return False

    _saveChunked(dest_path, stream)
    return True


def saveStreamTo(stream, dest_directory, autoExt=True, slug=easySlug):
    """Saves a file from a URL to a directory.
    
    Args:
        stream (TYPE): Description
        dest_directory (str): Local directory path
        autoExt (bool, optional): Automatically append an extension 
            based on the MIME type
    
    Returns:
        bool: Success
    """
    from os import path

    filename = slug(stream.url.split("/")[-1])

    if autoExt:
        filename_plain, ext = path.splitext(filename)
        if not ext:
            from ._data import mime2ext
            
            content_type = stream.headers.get("Content-Type")
            ext_match = mime2ext.get(content_type.split(";")[0], "")

            filename = filename_plain + ext_match

    dest_path = path.join(dest_directory, filename)
    return saveStreamAs(stream, dest_path)


def _saveChunked(path, response):
    """Save a binary stream to a path. Dumb.
    
    Args:
        path (str): 
        response (response): 
    """
    with open(path, 'wb') as file:
        for chunk in response:
            file.write(chunk)
