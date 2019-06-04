from PIL import Image


def framesInImage(im):  
    try:
        im = Image.open(im)
    except OSError:
        return -1
    try:
        while True:
            frames = im.tell() 
            im.seek(frames + 1)
    except EOFError:
        return frames + 1
