"""Networking functions
"""

import urllib.parse
import requests
import bs4
import os
from .filesystem import easySlug
from .stream import TriadLogger
import urllib.parse
import re

import atexit
import asyncio
import aiofiles
import aiohttp


OPTION_STRIPARGS = False

# Stateless helpers

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
    stream = requests.get(url, headers={"User-Agent": "curl/8.7.1"}, stream=True)
    try:
        stream.raise_for_status()
    except:
        print(stream, stream.content, stream.text, stream.headers)
        raise
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

    if OPTION_STRIPARGS:
        filename = slug(urllib.parse.urlparse(stream.url.split("/")[-1]).path) or ""
    else:
        filename = slug(stream.url.split("/")[-1])

    filename_plain, ext = path.splitext(filename)

    if len(filename_plain) > 120:
        print("Warning: Long filename", filename_plain)
        filename_plain = filename_plain[:120]

    if not filename_plain:
        # We are seeing the page from a directory, i.e. index.html
        url_parts = urllib.parse.urlsplit(stream.url)
        try:
            (dirname,) = re.search("/([^/]+)/$", stream.url).groups()
            dirname = slug(dirname)

            if indexHack:
                filename = path.join("..", dirname + ".html")
            else:
                filename = f"index{url_parts.query}.html"
        except AttributeError:
            coerce = f"index{url_parts.query}.html"
            print(f"stream.url: {stream.url} coerced to {coerce}")
            # There is no directory name
            return coerce
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
    try:
        with open(path, 'wb') as file:
            for chunk in response:
                file.write(chunk)
    except Exception:
        # Clean up partial file
        os.unlink(path)
        raise

def mirrorUrl(url, dest_directory, nc=False, slug=easySlug):
    return mirror(getStream(url), dest_directory, nc=nc, slug=slug)

def getMirrorDir(url, slug=easySlug):
    p = [slug(x) for x in url.split("/")]
    return os.path.join(*p[2:-1])

def mirror(stream, dest_directory, nc=False, slug=easySlug):
    dest_directory = os.path.join(dest_directory, getMirrorDir(stream.url, slug))
    os.makedirs(dest_directory, exist_ok=True)
    return saveStreamTo(stream, dest_directory, nc=nc, indexHack=False)

class AIODownloader(object):

    def __init__(self, nc=False, indexhack=True, stripargs=False):
        self.CHUNK_SIZE = 1024
        self.logger = TriadLogger(type(self).__name__)
        self.slug = easySlug

        self.no_clobber = nc
        self.indexhack = indexhack
        self.stripargs = stripargs

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        await self.session.close()
        return

    async def getResponse(self, url, prev_url=None):
        if prev_url:
            url = urllib.parse.urljoin(prev_url, url)
        response = await self.session.get(url)
        response.raise_for_status()
        return response

    async def saveChunked(self, file_path, response):
        try:
            # self.logger.info(f"Saving content to '{file_path}'")
            async with aiofiles.open(file_path, 'wb') as fd:
                async for data in response.content.iter_chunked(self.CHUNK_SIZE):
                    await fd.write(data)
            return True
        except Exception:
            os.unlink(file_path)
            self.logger.error(f"Fatal error saving to {file_path}")  # , exc_info=True)
            raise
            # return False

    async def saveAs(self, source, dest_path):
        if isinstance(source, str):
            # self.logger.info(f"Saving '{source}' as '{dest_path}'")
            async with await self.getResponse(source) as response:
                return await self.saveAs(response, dest_path)
        else:
            response = source

        response_length = float(response.headers.get("Content-Length", -1))
        if os.path.isfile(dest_path):
            if self.no_clobber:
                self.logger.info(f"Not overwriting same-name file at {dest_path}")
                return False
            if response_length == os.stat(dest_path).st_size:
                self.logger.info(f"Not overwriting same-size file at {dest_path} (size {response_length})")
                return False

        return await self.saveChunked(dest_path, response)

    async def saveTo(self, source, dest_dir, smart=True):
        if isinstance(source, str):
            async with await self.getResponse(source) as response:
                return await self.saveTo(response, dest_dir, smart=smart)
        else:
            response = source

        # Todo: May be better method for this?
        print(response)
        self.logger.info(response.url.path)
        filename = self.slug(response.url.path.split("/")[-1])
        if smart:
            filename = await self.getFilename(response)

        self.logger.info(f"Saving '{filename}' to '{dest_dir}'")

        dest_path = os.path.join(dest_dir, filename)
        await self.saveAs(response, dest_path)
        return dest_path

    async def getFilename(self, response):
        disposition = response.headers.get("content-disposition")
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
                    return self.slug(urllib.parse.unquote(filename))

        # Filename is the page name
        filename = self.slug(response.url.path.split("/")[-1])
        if self.stripargs:
            filename = urllib.parse.urlparse(filename).path or ""

        filename_plain, ext = os.path.splitext(filename)

        if len(filename_plain) > 120:
            self.logger.warning("Long filename", filename_plain)
            filename_plain = filename_plain[:120]

        # Page name may be "" (index.html)
        if filename == "":
            try:
                (dirname,) = re.search("/([^/]+)/$", response.url.path).groups()
                dirname = self.slug(dirname)

                if self.indexhack:
                    filename = os.path.join("..", dirname + ".html")
                else:
                    filename = "index.html"
            except Exception:
                self.logger.error(f"Can't puzzle response.url.path: {response.url.path}")
                raise
        elif not ext:
            # We have a page name, but not an extension.
            filename = filename_plain + self.guessExtension(response)
        return filename

    def guessExtension(self, response):
        from ._data import mime2ext
        content_type = response.headers.get("Content-Type")
        ext_match = mime2ext.get(content_type.split(";")[0], "")
        return ext_match
