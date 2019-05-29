# Flow control


def execif(function, args=tuple(), kwargs=dict(), condition=lambda f=None: bool(f)):
    """Shorthand. Executes a function with given args and kwargs if condition coerces to True.
    condition is a function of f, where f is the name of the function itself.

    This allows, amung other things, for function names to be set to None to disable them.

    Args:
        function (TYPE): Description
        args (TYPE, optional): Description
        kwargs (TYPE, optional): Description
        condition (function): Default: bool(function)
        function
        args (list)
        kwargs (dict)
    """
    if condition(function):
        function(*args, **kwargs)


def slow(iterable, delay):
    """A generator that simply throttles another generator or iterable.
    Note that this only throttles the generator, and may become invisible for slow functions.

    Args:
        iterable: Any generator or iterable that supports `for`
        delay (int): Number of seconds between cycles.

    Yields:
        next: type(next(iterable))
    """
    from time import time, sleep
    for next in iterable:
        last = time()
        yield next
        sleep(max(0, (delay - (time() - last))))

