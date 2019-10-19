import tkinter as tk
import traceback
from snip import loom
import snip.math
import snip.image
from PIL import Image
from PIL import ImageDraw
from PIL import ImageTk
from math import floor
import cv2
from tkinter import messagebox
import os
from threading import Lock


IMAGEEXTS = ["png", "jpg", "gif", "bmp", "jpeg", "tif", "gifv", "jfif"]
VIDEOEXTS = ["webm", "mp4", "mov"]
_IMAGEEXTS = ["." + e for e in IMAGEEXTS]
_VIDEOEXTS = ["." + e for e in VIDEOEXTS]


class ContentCanvas(tk.Canvas):
    def __init__(self, *args, **kwargs):
        """Args:
            parent (tk): Tk parent widget
            *args: Passthrough
            **kwargs: PassthroughphotoImageCache.pop
        """
        tk.Canvas.__init__(self, *args, **kwargs)

        self.photoImageCache = {}

        self.preloaderLock = Lock()

        # Initialize window
        self.initwindow()

    def initwindow(self):
        # set first image on canvas, an ImageTk.PhotoImage
        self.photoimage = self.create_image(
            0, 0, anchor=tk.N + tk.W)

    def markCacheDirty(self, entry):
        self.photoImageCache.pop(entry, None)

    def markAllDirty(self):
        self.photoImageCache.clear()

    def clear(self):
        self.itemconfig(self.photoimage, image=None)
        self.itemconfig(self.photoimage, state="hidden")

    def setFile(self, filepath):
        """Update the display to match the current image index.
        """

        maxwidth = self.winfo_width()
        maxheight = self.winfo_height()
        # Let window load
        if maxwidth == maxheight == 1:
            return self.after(200, self.setFile, filepath)

        try:
            self.curimg = self.makePhotoImage(filepath, maxwidth, maxheight)
        except (OSError, SyntaxError, tk.TclError) as e:
            print("[{}] Bad image: ".format(e) + filepath)
            traceback.print_exc()
            return False

        self.itemconfig(self.photoimage, image=self.curimg, state="normal")

        return True

    def preloadImage(self, filepaths):
        loom.thread(target=self._loadPhotoImage, args=(filepaths,))

    def _loadPhotoImage(self, filepaths):
        with self.preloaderLock:
            with loom.Spool(6) as spool:
                try:
                    for filepath in filepaths:
                        if filepath not in self.photoImageCache.keys():
                            print("caching", filepath)
                            spool.enqueue(
                                target=self.makePhotoImage,
                                args=(
                                    filepath,
                                    self.winfo_width(),
                                    self.winfo_height(),
                                )
                            )
                except (MemoryError, tk.TclError, ZeroDivisionError):
                    print(self.photoImageCache)
                    print(hex(id(self.photoImageCache)))
                    print(len(self.photoImageCache))
                    self.photoImageCache.clear()
                    raise

    def makePhotoImage(self, filename, maxwidth, maxheight, ALWAYS_RESIZE=True, stepsize=4):
        """Make a resized photoimage given a filepath

        Args:
            filename (str): Path to an image file
            maxwidth (TYPE): Maximum width of canvas
            maxheight (TYPE): Maximum height of canvas

        Returns:
            ImageTk.PhotoImage
        """
        # pilimg = Image.open(filename)

        pilimg = self.photoImageCache.get(filename)

        if pilimg:
            return ImageTk.PhotoImage(pilimg)

        with snip.math.timer("makePhotoImage {}".format(filename)):
            (filename_, fileext) = os.path.splitext(filename)
            canResize = True

            try:
                if fileext.lower() in _IMAGEEXTS:
                    pilimg = Image.open(filename)
                    pilimg = snip.image.autoRotate(pilimg)

                elif fileext.lower() in _VIDEOEXTS:
                    capture = cv2.VideoCapture(filename)
                    capture.grab()
                    flag, frame = capture.retrieve()
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pilimg = Image.fromarray(frame)
                else:
                    raise OSError("Exception reading image")
            except (cv2.error, OSError,):
                pilimg = Image.new('RGB', (10, 10), color=(0, 0, 0))
                ImageDraw.Draw(pilimg).text((2, 0), "?", fill=(255, 255, 255))

            imageIsTooBig = pilimg.width > maxwidth or pilimg.height > maxheight
            if (imageIsTooBig and canResize) or ALWAYS_RESIZE:
                ratio = min(maxwidth / pilimg.width, maxheight / pilimg.height)
                method = Image.ANTIALIAS

                if not imageIsTooBig:
                    stepratio = floor(ratio * stepsize) / stepsize
                    if stepratio != 0:
                        ratio = stepratio
                        method = Image.LINEAR
                    # else:
                    #     print("Warning: stepratio =", stepratio, "with ratio", ratio, "and stepsize", stepsize)
                try:
                    pilimg = pilimg.resize(
                        (int(pilimg.width * ratio), int(pilimg.height * ratio)), method)
                except (OSError, ValueError):
                    print("OS error resizing file", filename)
                    # loc = None
                    # for loc in locals():
                    #     print(loc, ":", locals().get(loc))
                    try:
                        return ImageTk.PhotoImage(pilimg)
                    except SyntaxError:
                        print("Corrupt image")
                        raise
                    except (MemoryError, tk.TclError):
                        print("Corrupt image, I think?")
                        print(filename)
                        messagebox.showwarning("Bad image", traceback.format_exc())
                        self.filepaths.remove(filename)
                        self.imageUpdate()

            self.photoImageCache[filename] = pilimg
            loom.thread(target=self.pruneImageCache, name="pruneImageCache")
        return ImageTk.PhotoImage(pilimg)

    def pruneImageCache(self, max_memory_entries=30):
        while len(self.photoImageCache) > max_memory_entries:
            self.photoImageCache.pop(list(self.photoImageCache.keys())[0])
        assert len(self.photoImageCache) <= max_memory_entries
