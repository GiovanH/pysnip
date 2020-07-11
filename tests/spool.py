import pytest
import time
import asyncio
import sys

from snip.loom import Spool, AIOSpool

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
        with Spool(8, "print bar") as spool:
            for i in range(0, 20):
                spool.enqueue(dowork, ([], 1, f"Saying {i}"))

        with Spool(8, "print", use_progbar=False) as spool:
            for i in range(0, 20):
                spool.enqueue(dowork, ([], 1, f"Saying {i}"))


class ATestData(object):

    async def test_fast(self):
        return

    async def test_slow(self):
        work = []

        max = 40

        async with AIOSpool(3, "slow") as spool:
            for i in range(0, max):
                spool.enqueue(adowork(work, i,))

        assert len(work) == max

    async def test_print(self):
        async with AIOSpool(8, "print bar") as spool:
            for i in range(0, 20):
                spool.enqueue(adowork([], 1, f"Saying {i}"))

        async with AIOSpool(8, "print", use_progbar=False) as spool:
            for i in range(0, 20):
                spool.enqueue(adowork([], 1, f"Saying {i}"))

async def adowork(work, i, say=None):
    time.sleep(.2)
    work.append(i)
    if say:
        print(say)

async def asynciomain():
    orig_out, orig_out_err = sys.stdout, sys.stderr
    await ATestData().test_fast()
    await ATestData().test_print()
    await ATestData().test_slow()
    await AIOSpool(jobs=[adowork([], 1, f"Saying hi")]).finish()
    assert orig_out is sys.stdout
    assert orig_out_err is sys.stderr


if __name__ == '__main__':
    orig_out, orig_out_err = sys.stdout, sys.stderr
    # TestData().test_fast()
    # TestData().test_print()
    # TestData().test_slow()
    assert orig_out is sys.stdout
    assert orig_out_err is sys.stderr
    asyncio.run(asynciomain())