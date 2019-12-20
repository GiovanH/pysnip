from snip.filesystem import Trash
import os
import glob

queue_size = 2
with Trash(queue_size=queue_size, verbose=True) as trash:
    for i in range(0, 10):
        open(f"test{i}.txt", "w").close()

    for i in range(0, 4):
        path = f"test{i}.txt"
        trash.delete(path)
        assert os.path.isfile(path)
        assert not trash.isfile(path)

    print(trash)
    print([f for f in glob.glob("test*.txt") if trash.isfile(f)])
    print(glob.glob("test*.txt"))
    trash.spool.finish(resume=True)
    assert glob.glob("test*.txt") == [f"test{i}.txt" for i in range(2, 10)]

for i in range(0, 10):
    try:
        os.unlink(f"test{i}.txt")
    except FileNotFoundError:
        pass
