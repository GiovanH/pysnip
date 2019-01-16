# pylib

Shared libraries for my personal work.

## jfileutil.py

Simple file pickling functionality for storing and loading JSON objects.

## loom.py

Provides threading capabilities, including Spools, which allow for powerful, simple, grouped threading implementation in very simple statements. 

```python
import loom

work = []
spool = loom.Spool(4)	# Initialize a Spool with a quota size of 4.

for i in range(0, 10):
    spool.enqueue(target=work.append, args=(i,))
# At this point in the code, up to 4 threads will be running to finish this job.
assert (len(work) >= 0) and (len(work) <= 10) # This is guarenteed. 

spool.finish()  # Block the current code until each job is complete.
assert len(work) == 10  # This is also guarenteed. 
```

You can also use threads as context managers, allowing them to finish themselves appropriately. 

```python
import loom

work = []
with loom.Spool(4) as spool:	# Initialize a Spool with a quota size of 4.
    for i in range(0, 10):
        spool.enqueue(target=work.append, args=(i,))
    # At this point in the code, up to 4 threads will be running to finish this job.
    assert (len(work) >= 0) and (len(work) <= 10) # This is guarenteed. 
# At the end of the context session, Spool will finish its work before continuing. No manual .finish() call required.
assert len(work) == 10  # This is also guarenteed. 
```

Behind the scenes, loom is doing the following:

- Maintaining a queue of tasks
- Starting tasks to maximize running threads without exceeding its quota
- Maintaining a list of live threads it started
- Waiting for its threads to finish, and dequeuing more threads if appropriate

Spools also have the ability to

- Ensure all running tasks finish before starting more threads, by request

## tkit.py

Additional tkinter widgets and utility functions for GUI programming

### `JSONEditor`

A user-friendly GUI that allows live manipulation of JSON data by the user. Designed for use as a settings editor. Uses tabbed views and supports the full json standard, including lists and nested dictionaries.

### `MultiColumnListbox`

A widget that uses the ttk.TreeView widget as a fully interactive table

### `ToggleButton`

A subclass of ttk.Checkbutton that acts as a simple interface for Metro/Material/iOS style toggle switches.