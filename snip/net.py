"""Networking functions
"""

from urllib.parse import urljoin
import requests
import bs4
from .filesystem import easySlug


def queryUrlToDict(url):
    from urllib.parse import urlparse, parse_qs
    # print(urlparse(url))
    # print(urlparse(url).query)
    # print(parse_qs(urlparse(url).query))
    return parse_qs(urlparse(url).query)


def queryDictToUrlSuffix(querydict):
    from urllib.parse import urlencode, quote_plus
    return urlencode(querydict, quote_via=quote_plus)


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
    stream.raise_for_status()
    return stream


def saveStreamAs(stream, dest_path, nc=False, verbose=False):
    """Save a URL to a path as file

    Args:
        stream (stream): Stream
        dest_path (str): Local path

    Returns:
        bool: Success
    """
    from os import path, stat
    from math import inf

    stream_length = float(stream.headers.get("Content-Length", -1))
    if path.isfile(dest_path):
        if nc:
            return False
        if stream_length == stat(dest_path).st_size:
            if verbose:
                print("Not overwriting same-size file at", dest_path)
            return False
        else:
            if verbose:
                print("File sizes do not match for output", dest_path, ":", stream_length, "!=", stat(dest_path).st_size)

    _saveChunked(dest_path, stream)
    return True


def getFilename(stream, indexHack=True, slug=easySlug):
    # Cases to consider:
    # /(index.html)
    # /document
    # /document.pdf
    from os import path
    import re

    filename = easySlug(stream.url.split("/")[-1])
    (dirname,) = re.search("/([^/]+)/$", stream.url).groups()
    dirname = easySlug(dirname)
    filename_plain, ext = path.splitext(filename)

    if not filename_plain:
        # We are seeing the page from a directory, i.e. index.html
        if indexHack:
            filename_plain = path.join("..", dirname + ".html")
        else:
            filename_plain = "index"
    if not ext:
        filename_plain = filename_plain + guessExtension(stream)
    return filename_plain

def guessExtension(stream):
    from ._data import mime2ext
    content_type = stream.headers.get("Content-Type")
    ext_match = mime2ext.get(content_type.split(";")[0], "")
    return ext_match
    


def saveStreamTo(stream, dest_directory, autoExt=True, nc=False, verbose=False, slug=easySlug):
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
        filename = getFilename(stream, slug=slug)

    dest_path = path.join(dest_directory, filename)
    return saveStreamAs(stream, dest_path, nc=nc, verbose=verbose)


def _saveChunked(path, response):
    """Save a binary stream to a path. Dumb.

    Args:
        path (str): 
        response (response): 
    """
    with open(path, 'wb') as file:
        for chunk in response:
            file.write(chunk)
