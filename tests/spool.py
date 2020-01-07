import pytest
import time

from snip.loom import Spool

print('good day and welcome to tests')

def dowork(work, i, say=None):
    time.sleep(1)
    work.append(i)
    if say:
        print(say)

class TestData(object):

    def test_fast(self):
        work = []
        with Spool(8, "fast") as spool:
            for i in range(0, 20):
                spool.enqueue(work.append, (i,))

        assert len(work) == 20

    def test_slow(self):
        work = []

        max = 40

        with Spool(3, "slow") as spool:
            for i in range(0, max):
                spool.enqueue(dowork, (work, i,))

        assert len(work) == max

    def test_print(self):
        with Spool(8, "print") as spool:
            for i in range(0, 20):
                spool.enqueue(dowork, ([], 1, f"Saying {i}"))



if __name__ == '__main__':
    TestData().test_fast()
    TestData().test_print()
    TestData().test_slow()
