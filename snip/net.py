"""Networking functions
"""

import urllib.parse
import requests
import bs4
import os
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
    url = urllib.parse.urljoin(prev_url, url)
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
    url = urllib.parse.urljoin(prev_url, url)
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

    disposition = stream.headers.get("content-disposition")
    if disposition:
        # If the response has Content-Disposition, try to get filename from it
        cd = dict(
            map(
                lambda x: x.strip().split('=') if '=' in x else (x.strip(), ''),
                disposition.split(';')
            )
        )
        if 'filename' in cd:
            filename = urllib.parse.unquote(cd['filename'].strip("\"'"))
            if filename:
                return slug(urllib.parse.unquote(filename))

    filename = slug(stream.url.split("/")[-1])
    filename_plain, ext = path.splitext(filename)

    if not filename_plain:
        # We are seeing the page from a directory, i.e. index.html
        (dirname,) = re.search("/([^/]+)/$", stream.url).groups()
        dirname = slug(dirname)

        if indexHack:
            filename = path.join("..", dirname + ".html")
        else:
            filename = "index.html"
    elif not ext:
        filename = filename_plain + guessExtension(stream)
    return filename


def guessExtension(stream):
    from ._data import mime2ext
    content_type = stream.headers.get("Content-Type")
    ext_match = mime2ext.get(content_type.split(";")[0], "")
    return ext_match


def saveStreamTo(stream, dest_directory, autoExt=True, nc=False, verbose=False, slug=easySlug, indexHack=True):
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
        filename = getFilename(stream, slug=slug, indexHack=indexHack)

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


def mirrorUrl(url, dest_directory, nc=False, slug=easySlug):
    return mirror(getStream(url), dest_directory, nc=nc, slug=slug)

def getMirrorDir(url, slug=easySlug):
    p = [slug(x) for x in url.split("/")]
    return os.path.join(*p[2:-1])

def mirror(stream, dest_directory, nc=False, slug=easySlug):
    dest_directory = os.path.join(dest_directory, getMirrorDir(stream.url, slug))
    os.makedirs(dest_directory, exist_ok=True)
    return saveStreamTo(stream, dest_directory, nc=nc, indexHack=False)
