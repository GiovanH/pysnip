"""Summary
"""
from urllib.parse import urljoin
import requests
import bs4


def getSoup(url, prev_url=None):
    """Get a BeautifulSoup object from a URL

    Args:
        url (str)
        prev_url (str, optional): Previous url, for relative resolution

    Returns:
        soup: Beautiful Soup
    """
    url = urljoin(prev_url, url)
    resp = requests.get(url)
    resp.raise_for_status()
    soup = bs4.BeautifulSoup(resp.text, features="html.parser")
    return soup


def saveAs(url, dest_path, prev_url=None, session=requests):
    """Save a URL to a path as file

    Args:
        url (str): Source URL
        dest_path (str): Local path
        prev_url (str, optional): Previous URL, for relative resolution
        session (requests.Session, optional): Session for persistance

    Returns:
        TYPE: Description
    """
    from os import path, stat
    from math import inf
    url = urljoin(prev_url, url)

    stream = session.get(url, stream=True)
    stream_length = stream.headers.get("Content-Length", inf)
    if path.isfile(dest_path) and stream_length == stat(dest_path).st_size:
        return False

    _saveChunked(dest_path, stream)
    return True


def saveTo(url, dest_directory, prev_url=None, session=requests, autoExt=True):
    """Saves a file from a URL to a directory.

    Args:
        url (str): Remote URL to file
        dest_directory (str): Local directory path
        prev_url (str, optional): Previous URL for relative paths
        session (requests.Session, optional): Session object for persistance

    Returns:
        bool: Success
    """
    from os import path
    from .filesystem import easySlug

    filename = easySlug(url.split("/")[-1])

    if autoExt:
        filename_plain, ext = path.splitext(filename)
        if not ext:
            from ._data import mime2ext
            
            content_type = session.get(url).headers.get("Content-Type")
            ext_match = mime2ext.get(content_type.split(";")[0], "")

            filename = filename_plain + ext_match

    dest_path = path.join(dest_directory, filename)
    return saveAs(url, dest_path, prev_url=prev_url, session=session)


def _saveChunked(path, response):
    """Save a binary stream to a path. Dumb.

    Args:
        path (str)
        response (response)
    """
    with open(path, 'wb') as file:
        for chunk in response:
            file.write(chunk)
