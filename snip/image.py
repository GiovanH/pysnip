from PIL import Image
from PIL import ExifTags


def framesInImage(im):  
    try:
        im = Image.open(im)
    except OSError:
        return 1
    try:
        while True:
            frames = im.tell() 
            im.seek(frames + 1)
    except EOFError:
        return frames + 1


def autoRotate(image):

    orientationflags = [key for key in ExifTags.TAGS.keys() if ExifTags.TAGS[key] == 'Orientation']
    try:
        for orientation in orientationflags:
            exif = dict(image._getexif().items())
            if not exif.get(orientation):
                continue

            if exif[orientation] == 3:
                return image.rotate(180, expand=True)
            elif exif[orientation] == 6:
                return image.rotate(270, expand=True)
            elif exif[orientation] == 8:
                return image.rotate(90, expand=True)
    except (KeyError, AttributeError):
        pass

    return image
