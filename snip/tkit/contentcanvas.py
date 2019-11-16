import tkinter as tk
import traceback
from snip import loom
import snip.math
import snip.image
import snip.strings
from PIL import Image
from PIL import ImageDraw
from PIL import ImageTk
from math import floor
import cv2
from tkinter import messagebox
import os
from threading import Lock
from tkinter import filedialog
import subprocess
import threading
import datetime


IMAGEEXTS = ["png", "jpg", "gif", "bmp", "jpeg", "tif", "gifv", "jfif"]
VIDEOEXTS = ["webm", "mp4", "mov"]
_IMAGEEXTS = ["." + e for e in IMAGEEXTS]
_VIDEOEXTS = ["." + e for e in VIDEOEXTS]


def copy_to_clipboard(filepath):
    from io import BytesIO
    import win32clipboard
    from PIL import Image

    def send_to_clipboard(clip_type, data):
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(clip_type, data)
        win32clipboard.CloseClipboard()

    image = Image.open(filepath)

    output = BytesIO()
    image.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()

    send_to_clipboard(win32clipboard.CF_DIB, data)


class ContentCanvas(tk.Canvas):
    def __init__(self, *args, **kwargs):
        """Args:
            parent (tk): Tk parent widget
            *args: Passthrough
            **kwargs: PassthroughphotoImageCache.pop
        """
        tk.Canvas.__init__(self, *args, **kwargs)

        self.photoImageCache = {}
        self.textCache = {}

        self.preloaderLock = Lock()

        self.current_file = ""

        # Initialize window
        self.initwindow()

    def initwindow(self):
        # set first image on canvas, an ImageTk.PhotoImage
        self.photoimage = self.create_image(
            0, 0, anchor="nw")

        self.text = self.create_text(10, 10, anchor="nw")

        self.bind("<Configure>", self.onResize)

        # create a menu
        popup = tk.Menu(self, tearoff=0)
        popup.add_command(label="Copy to clipboard", command=lambda: copy_to_clipboard(self.current_file))  # , command=next) etc...
        popup.add_separator()
        popup.add_command(label="Open", command=lambda: os.startfile(self.current_file))
        popup.add_command(label="Open file location", command=self.open_file_location)
        popup.add_separator()
        popup.add_command(label="Save a copy", command=self.save_a_copy)
        popup.add_command(label="Save a copy (quick)", command=self.quicksave)

        def do_popup(event):
            # display the popup menu
            try:
                popup.tk_popup(event.x_root, event.y_root, 0)
            finally:
                # make sure to release the grab (Tk 8.0a1 only)
                popup.grab_release()

        self.bind("<Button-3>", do_popup)

    def open_file_location(self):
        FILEBROWSER_PATH = os.path.join(os.getenv('WINDIR'), 'explorer.exe')
        path = os.path.normpath(self.current_file)

        if os.path.isdir(path):
            subprocess.run([FILEBROWSER_PATH, path])
        elif os.path.isfile(path):
            subprocess.run([FILEBROWSER_PATH, '/select,', os.path.normpath(path)])

    def save_a_copy(self):
        newFileName = filedialog.asksaveasfilename(
            initialfile=os.path.basename(self.current_file)
        )
        snip.filesystem.copyFileToFile(self.current_file, newFileName)

    def quicksave(self, event=None):
        downloads = snip.filesystem.userProfile("Downloads")
        snip.filesystem.copyFileToDir(self.current_file, downloads)
        self.bell()

    def onResize(self, *args):
        # self.markAllDirty()
        # We don't need to mark text dirty
        self.photoImageCache.clear()
        self.setFile(self.current_file)

    def markCacheDirty(self, entry):
        self.photoImageCache.pop(entry, None)
        self.textCache.pop(entry, None)

    def markAllDirty(self):
        self.photoImageCache.clear()
        self.textCache.clear()

    def clear(self):
        self.itemconfig(self.photoimage, image=None)
        self.itemconfig(self.photoimage, state="hidden")

    def setFile(self, filepath):
        """Update the display to match the current image index.
        """

        self.current_file = filepath

        # try:
        #     self.curimg = self.makePhotoImage(filepath)
        # except (OSError, SyntaxError, tk.TclError) as e:
        #     print("[{}] Bad image: ".format(e) + filepath)
        #     traceback.print_exc()
        #     return False

        self.configureForFile(filepath)

        return True

    def configureForFile(self, filepath):
        text = None

        (filename_, fileext) = os.path.splitext(filepath)
        if fileext.lower() in _IMAGEEXTS or fileext.lower() in _VIDEOEXTS:
            self.curimg = self.makePhotoImage(filepath)
            self.itemconfig(self.photoimage, image=self.curimg, state="normal")
            self.itemconfig(self.text, text=None, state="hidden")
        else:
            text = self.makeTextData(filepath)
            self.itemconfig(self.text, text=text, state="normal")
            self.itemconfig(self.photoimage, image="", state="hidden")
            self.curimg = None

    def preloadImage(self, filepaths):
        for filepath in filepaths:
            if filepath not in self.photoImageCache.keys():
                threading.Thread(
                    target=self.makePhotoImage,
                    args=(
                        filepath,
                        self.winfo_width(),
                        self.winfo_height(),
                    )
                ).start()
        # return
        # with self.preloaderLock:
        #     with loom.Spool(6, cfinish=dict(use_pbar=False)) as spool:
        #         try:
        #             for filepath in filepaths:
        #                 if filepath not in self.photoImageCache.keys():
        #                     print("caching", filepath)
        #                     spool.enqueue(
        #                         target=self.makePhotoImage,
        #                         args=(
        #                             filepath,
        #                             self.winfo_width(),
        #                             self.winfo_height(),
        #                         )
        #                     )
        #         except (MemoryError, tk.TclError, ZeroDivisionError):
        #             print(self.photoImageCache)
        #             print(hex(id(self.photoImageCache)))
        #             print(len(self.photoImageCache))
        #             self.photoImageCache.clear()
        #             raise

    def makeTextData(self, filepath):
        text = self.textCache.get(filepath, "")
        if not text:
            text += f"\nPath:\t{filepath}"
            text += f"\nSize:\t{snip.strings.bytes_to_string(os.path.getsize(filepath))}"

            filename, fileext = os.path.splitext(filepath)
            if fileext.lower() == ".pdf":
                try:
                    from pdfminer.pdfparser import PDFParser
                    from pdfminer.pdfdocument import PDFDocument

                    def decodePdfVal(value):
                        try:
                            # if value.startswith(b"D:"):
                            # Handle dates?
                            # PDF standard is D:YYYYMMDDHHmmSSOHH'mm'

                            return value.decode(errors="replace")
                        except Exception as e:
                            print(e)
                            return value

                    with open(filepath, "rb") as fp:
                        parser = PDFParser(fp)
                        doc = PDFDocument(parser)

                        for infoblock in doc.info:
                            print(infoblock)
                            for key, value in infoblock.items():
                                text += f"\n{key}:\t{decodePdfVal(value)}"

                except ImportError:
                    text += f"\nImportError: pdfminer not installed"
                except Exception as e:
                    text += f"\npdfminer {type(e)}: {e}"

            if os.name == "nt":
                from snip.win32_fileprops import property_sets
                for name, properties in property_sets(filepath):
                    text += f"\nWin32 {name}"
                    for key, value in properties.items():
                        if value:
                            text += f"\n\t{key}:\t{value}"

            try:
                with open(filepath, "r") as fp:
                    text += f"\n{fp.read(800000)}"
            except Exception as e:
                print(e)
                pass

        self.textCache[filepath] = text
        return text

    def makePhotoImage(self, filename, ALWAYS_RESIZE=True, stepsize=4):
        """Make a resized photoimage given a filepath

        Args:
            filename (str): Path to an image file
            maxwidth (TYPE): Maximum width of canvas
            maxheight (TYPE): Maximum height of canvas

        Returns:
            ImageTk.PhotoImage
        """
        # pilimg = Image.open(filename)

        maxwidth = self.winfo_width()
        maxheight = self.winfo_height()
        # Let window load
        if maxwidth == maxheight == 1:
            self.after(200, self.makePhotoImage, filename, ALWAYS_RESIZE, stepsize)

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
                    # print(f"Resize: ratio {ratio}, method {method}, stepsize {stepsize}\n{filename}")
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
