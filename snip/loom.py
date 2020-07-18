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
import asyncio
from tqdm.contrib import DummyTqdmFile
import warnings


class ThreadSpool():

    """A spool is a queue of threads.
    This is a simple way of making sure you aren't running too many threads at one time.
    At intervals, determined by `delay`, the spooler (if on) will start threads from the queue.
    The spooler can start multiple threads at once.

    You can .print to this object, and it will intelligently print the arguments
    based on whether or not it's using a progress bar.
    """

    def __init__(self, quota=8, name="Spool", belay=False, use_progbar=True):
        """Create a spool

        Args:
            quota (int): Size of quota, i.e. how many threads can run at once.
            cfinish (dict, optional): Description
        """
        super(Spool, self).__init__()
        self.quota = quota
        self.name = name
        self.use_progbar = use_progbar

        self.queue = []
        self.started_threads = []

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
        try:
            self.finish(resume=False)
        except KeyboardInterrupt:
            raise

    def __str__(self):
        return f"{type(self)} at {hex(id(self))}: {self.numRunningThreads}/{self.quota} threads running with {len(self.queue)} queued."

    # Interfaces

    def print(self, *args, **kwargs):
        if self.progbar:
            self.progbar.write(
                kwargs.get("sep", " ").join(args)
            )
        else:
            print(*args, **kwargs)

    def start(self):
        """Begin spooling threads in the background, if not already doing so. 
        """
        self.background_spool = True
        if not (self.spoolThread and self.spoolThread.is_alive()):
            self.spoolThread = threading.Thread(target=self.spoolLoop, name="Spooler")
            self.spoolThread.start()

    def cancel(self):
        """Abort immeditately, potentially without finishing threads.
        """
        self.queue.clear()
        self.finish()

    def finish(self, resume=False, verbose=False, use_pbar=None):
        """Block and complete all threads in queue.

        Args:
            resume (bool, optional): Resume spooling after finished
            verbose (bool, optional): Report progress towards queue completion.
            use_pbar (bool, optional): Graphically display progress towards queue completions
        """
        if use_pbar is None:
            use_pbar = self.use_progbar

        # Stop existing spools
        self.background_spool = False
        self.dirty.set()

        if verbose:
            print(self)

        # Progress bar management, optional.
        def updateProgressBar():
            # Update progress bar.
            if use_pbar:
                q = (len(self.queue) if self.queue else 0)
                progress = (self._pbar_max - (self.numRunningThreads + q))

                progbar.total = self._pbar_max
                progbar.n = progress
                progbar.set_postfix(queue=q, running=f"{self.numRunningThreads:2}/{self.quota}]")
                progbar.update(0)

        self._pbar_max = self.numRunningThreads + len(self.queue)

        if self._pbar_max > 0:

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
                    self.doSpool(verbose=False)
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
                print("Aborting spooled thread", file=sys.stderr)
                traceback.print_exc()
            finally:
                self.dirty.set()
        self.queue.append(threading.Thread(target=runAndFlag, *thargs, **thkwargs))
        self._pbar_max += 1
        self.dirty.set()

    def setQuota(self, newQuota):
        self.quota = newQuota
        self.dirty.set()

    ##################
    # Minor utility
    ##################

    def startThread(self, newThread):
        self.started_threads.append(newThread)
        newThread.start()
        self.dirty.set()

    @property
    def numRunningThreads(self):
        """Accurately count number of "our" running threads.

        Returns:
            int: Number of running threads owned by this spool
        """
        return len([
            thread
            for thread in self.started_threads
            if thread.is_alive()
        ])

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
        while len(self.queue) > 0 and self.quota - self.numRunningThreads > 0:
            if verbose:
                print(self)
            # for i in range(threads_to_queue):
            try:
                self.startThread(self.queue.pop())
            except IndexError:
                print(f"IndexError: Popped from empty queue?\nWhile queueing thread {len(self.queue)}-{self.quota}-{self.numRunningThreads}")
                break
            # threads_to_queue = min(len(self.queue), self.quota - self.numRunningThreads)

        self.dirty.clear()



class AIOSpool():

    """A spool is a queue of threads.
    This is a simple way of making sure you aren't running too many threads at one time.
    At intervals, determined by `delay`, the spooler (if on) will start threads from the queue.
    The spooler can start multiple threads at once.

    You can .print to this object, and it will intelligently print the arguments
    based on whether or not it's using a progress bar.
    """

    def __init__(self, quota=8, jobs=[], name="AIOSpool", use_progbar=True):
        """Create a spool

        Args:
            quota (int): Size of quota, i.e. how many threads can run at once.
            cfinish (dict, optional): Description
        """
        self.name = name
        self.use_progbar = use_progbar
        self.quota = quota

        self.started_threads = []
        self.queue = []

        self._pbar_max = 0

        self.nop = (lambda: None)
        self.on_finish_callbacks = [
            self._on_finish_callback
        ]

        if type(jobs) == int:
            warnings.warn("Jobs should be iterable, not an int! You're using queue syntax!")
            jobs = []

        if iter(jobs) and type(jobs) is not str:
            for job in jobs:
                self.enqueue(job)
        else:
            warnings.warn("Jobs should be iterable! You're using the wrong init syntax!")
            

    async def __aenter__(self):
        return self

    async def __aexit__(self, type, value, traceback):
        try:
            return await self.finish(resume=False)
        except KeyboardInterrupt:
            raise

    def __str__(self):
        return f"{type(self)} at {hex(id(self))}: {self.numActiveJobs} active jobs."

    # Interfaces

    def print(self, *args, **kwargs):
        if self.progbar:
            self.progbar.write(
                kwargs.get("sep", " ").join(args)
            )
        else:
            print(*args, **kwargs)

    async def finish(self, resume=False, verbose=False, use_pbar=None):
        """Block and complete all threads in queue.
        
        Args:
            resume (bool, optional): Resume spooling after finished
            verbose (bool, optional): Report progress towards queue completion.
            use_pbar (bool, optional): Graphically display progress towards queue completions
        """
        if use_pbar is None:
            use_pbar = self.use_progbar

        if verbose:
            print(self)

        # Progress bar management, optional.
        # Wrap the existing callback
        def updateProgressBar():
            # Update progress bar.
            if use_pbar:
                q = (len(self.queue) if self.queue else 0)
                progress = (self._pbar_max - (self.numActiveJobs + q))

                progbar.total = self._pbar_max
                progbar.n = progress
                progbar.set_postfix(queue=q, waiting=f"{self.numActiveJobs:2}]")
                progbar.update(0)
        
        self.on_finish_callbacks.insert(0, updateProgressBar)

        self._pbar_max = self.numActiveJobs + len(self.queue)

        if self._pbar_max > 0:
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

                while self.numActiveJobs:
                    await asyncio.gather(*self.started_threads)
                updateProgressBar()

                assert self.numActiveJobs == 0, "Finished without finishing all threads"
            finally:
                if use_pbar:
                    progbar.close()
                    sys.stdout, sys.stderr = orig_out_err

        if verbose:
            print(self)

        self.on_finish_callbacks.remove(updateProgressBar)

    def on_finish_callback(self):
        for c in self.on_finish_callbacks:
            c()

    def _on_finish_callback(self):
        # While there is a queue
        # This gets called from an ending job, so we don't count that one.
        while len(self.queue) > 0 and (self.numActiveJobs - 1) < self.quota:
            try:
                # print(f"Starting job {len(self.queue)=} {self.numActiveJobs=} {self.quota=}")
                future = self.queue.pop()
                self.started_threads.append(asyncio.ensure_future(future))
                
            except IndexError:
                print(f"IndexError: Popped from empty queue?\nWhile queueing thread {len(self.queue)}-{self.quota}-{self.numRunningThreads}")
                break
            # threads_to_queue = min(len(self.queue), self.quota - self.numRunningThreads)

    def enqueue(self, target):
        """Add a thread to the back of the queue.

        Args:
            target (function): The function to execute
            name (str): Name of thread, for debugging purposes
            args (tuple, optional): Description
            kwargs (dict, optional): Description

            *thargs: Args for threading.Thread
            **thkwargs: Kwargs for threading.Thread
        """
        async def runAndFlag():
            try:
                await target
                self.on_finish_callback()
            except Exception:
                print("Aborting spooled job", file=sys.stderr)
                traceback.print_exc()
        self.queue.append(runAndFlag())
        self._pbar_max += 1
        self.on_finish_callback()

    ##################
    # Minor utility
    ##################

    @property
    def numActiveJobs(self):
        """Accurately count number of "our" running threads.

        Returns:
            int: Number of running threads owned by this spool
        """
        return len([
            thread
            for thread in self.started_threads
            if not thread.done()
        ])


Spool = ThreadSpool
