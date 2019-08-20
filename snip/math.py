# Math

from contextlib import contextmanager


@contextmanager
def timer(label="task"):
    import time
    start_time = time.time()

    try:
        yield None
    finally:
        time_taken = time.time() - start_time
        print("Processed", label, "in", time_taken, "secs")


def bytes_to_string(bytes, units=['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB'], sep="", base=1024):
    """ Returns a human readable string reprentation of bytes."""
    # Adapted from a comment by "Mr. Me" on github.
    if bytes < base:
        return "{:0.2f}{}{}".format(bytes, sep, units[0])
    else:
        return bytes_to_string(bytes / base, units[1:], sep=sep)
