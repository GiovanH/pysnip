#!/bin/python3
"""Summary

Attributes:
    necessary_threads (int): Description
    necessary_threads : int
    Description
"""

import threading
import tqdm
import traceback
import contextlib
import sys
from tqdm.contrib import DummyTqdmFile


def thread(target, *args, **kwargs):
    """Initialize and start a thread

    Args:
        target (function): Task to complete
        *args: Passthrough to threading.Thread
        **kwargs: threading.Thread
    """
    t = threading.Thread(target=target, *args, **kwargs)
    t.start()


class Spool():

    """A spool is a queue of threads.
    This is a simple way of making sure you aren't running too many threads at one time.
    At intervals, determined by `delay`, the spooler (if on) will start threads from the queue.
    The spooler can start multiple threads at once.
    """

    def __init__(self, quota, name="Spool", cfinish={}, belay=False):
        """Create a spool

        Args:
            quota (int): Size of quota, i.e. how many threads can run at once.
            cfinish (dict, optional): Description
        """
        super(Spool, self).__init__()
        self.quota = quota
        self.name = name
        self.cfinish = cfinish

        self.queue = []
        self.running_threads = []

        self.flushing = 0
        self._pbar_max = 0
        self.spoolThread = None
        self.background_spool = False
        self.dirty = threading.Event()

        if not belay:
            self.start()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.finish(resume=False, **self.cfinish)

    def __str__(self):
        return f"{type(self)} at {hex(id(self))}: {self.numRunningThreads}/{self.quota} threads running with {len(self.queue)} queued."

    # Interfaces

    def print(self, *objs, **kwargs):
        if self.progbar:
            self.progbar.write(
                kwargs.get("sep", " ").join(objs)
            )
        else:
            print(*objs, **kwargs)

    def start(self):
        """Begin spooling threads in the background, if not already doing so. 
        """
        self.background_spool = True
        if not (self.spoolThread and self.spoolThread.is_alive()):
            self.spoolThread = threading.Thread(target=self.spoolLoop, name="Spooler")
            self.spoolThread.start()

    def finish(self, resume=False, verbose=False, use_pbar=True):
        """Block and complete all threads in queue.

        Args:
            resume (bool, optional): Resume spooling after finished
            verbose (bool, optional): Report progress towards queue completion.
            use_pbar (bool, optional): Graphically display progress towards queue completions
        """
        # Stop existing spools
        self.background_spool = False
        self.dirty.set()

        if verbose:
            print(self)

        # Progress bar management, optional.
        def updateProgressBar():
            # Update progress bar.
            q = (len(self.queue) if self.queue else 0)
            progress = (self._pbar_max - (self.numRunningThreads + q))

            progbar.total = self._pbar_max
            progbar.n = progress
            progbar.set_postfix(queue=q, running=f"{self.numRunningThreads:2}/{self.quota}]")
            progbar.update(0)

        self._pbar_max = self.numRunningThreads + len(self.queue)

        try:
            if use_pbar:
                orig_out_err = sys.stdout, sys.stderr
                sys.stdout, sys.stderr = map(DummyTqdmFile, orig_out_err)
                self.progbar = progbar = tqdm.tqdm(
                    file=orig_out_err[0], dynamic_ncols=True,
                    desc=self.name,
                    total=self._pbar_max,
                    unit="job"
                )

                updateProgressBar()
            # assert not self.spoolThread.isAlive, "Background loop did not terminate"
            # Create a spoolloop, but block until it deploys all threads.
            while (self.queue and len(self.queue) > 0) or (self.numRunningThreads > 0):
                self.dirty.wait()
                threads_to_queue = min(len(self.queue), self.quota - self.numRunningThreads)
                if verbose:
                    print(self)
                for i in range(threads_to_queue):
                    try:
                        self.startThread(self.queue.pop(0))
                    except IndexError:
                        print(f"IndexError: Popped from empty queue?\nWhile queueing thread {i} of {threads_to_queue}\n{len(self.queue)}-{self.quota}-{self.numRunningThreads}")
                if use_pbar:
                    updateProgressBar()
                self.dirty.set()
            updateProgressBar()

            assert len(self.queue) == 0, "Finished without deploying all threads"
            assert self.numRunningThreads == 0, "Finished without finishing all threads"
        finally:
            if use_pbar:
                progbar.close()
                sys.stdout, sys.stderr = orig_out_err

        if resume:
            self.queue.clear()  # Create a fresh queue
            self.start()

        if verbose:
            print(self)

    def flush(self):
        """Start and finishes all current threads before starting any new ones. 
        """
        self.flushing = 1

    def enqueue(self, target, args=tuple(), kwargs=dict(), *thargs, **thkwargs):
        """Add a thread to the back of the queue.

        Args:
            target (function): The function to execute
            name (str): Name of thread, for debugging purposes
            args (tuple, optional): Description
            kwargs (dict, optional): Description

            *thargs: Args for threading.Thread
            **thkwargs: Kwargs for threading.Thread
        """
        def runAndFlag():
            try:
                target(*args, **kwargs)
            except Exception:
                traceback.print_exc()
            finally:
                self.dirty.set()
        self.queue.append(threading.Thread(target=runAndFlag, *thargs, **thkwargs))
        self._pbar_max += 1
        self.dirty.set()

    def setQuota(self, newQuota):
        self.quota = newQuota
        self.dirty.set()

    def enqueueSeries(self, targets):
        """Queue a series of tasks that are interdepenent. 
        Just a wrapper that creates a closure around functions, then queues them.

        Args:
            targets (list): A list of functions
        """
        def closure():
            for target in targets:
                target()
            self.dirty.set()
        self.queue.append(threading.Thread(target=closure))
        self.dirty.set()

    ##################
    # Minor utility
    ##################

    def startThread(self, newThread):
        self.running_threads.append(newThread)
        newThread.start()
        self.dirty.set()

    @property
    def numRunningThreads(self):
        """Accurately count number of "our" running threads.
        This prunes dead threads and returns a count of live threads.

        Returns:
            int: Number of running threads owned by this spool
        """
        self.running_threads = [
            thread
            for thread in self.running_threads
            if thread.is_alive()
        ]
        return len(self.running_threads)

    ##################
    # Spooling
    ##################

    def spoolLoop(self, verbose=False):
        """Periodically start additional threads, if we have the resources to do so.
        This function is intended to be run as a thread.
        Runs until the queue is empty or, if self.background_spool is true, runs forever.

        Args:
            verbose (bool, optional): Report progress towards queue completion.
        """
        while True:
            self.dirty.wait()
            if not self.background_spool:
                break
            #   self.dirty.set()
            self.doSpool(verbose=verbose)

    def doSpool(self, verbose=False):
        """Spools new threads until the queue empties or the quota fills.

        Args:
            verbose (bool, optional): Verbose output
        """

        if self.flushing == 1:
            # Finish running threads
            if self.numRunningThreads == 0:
                self.flushing = 0
            else:
                self.dirty.clear()
                return

        # Start threads until we've hit quota, or until we're out of threads.
        # threads_to_queue =
        while min(len(self.queue), self.quota - self.numRunningThreads) > 0:
            if verbose:
                print(self)
            # for i in range(threads_to_queue):
            self.startThread(self.queue.pop(0))
            # threads_to_queue = min(len(self.queue), self.quota - self.numRunningThreads)

        self.dirty.clear()
