import pytest
import time

from snip.loom import Spool

print('good day and welcome to tests')

def dowork(work, i):
    time.sleep(1)
    work.append(i)

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

    def test_purge(self):

        import snip.jfileutil as ju

        default = { k: k for k in range(0, 2000) }

        print("Removing dead hashes")

        def _pruneKey(dictionary, key):
            return 1
            # if purge:
            #     for p in dictionary[key]:
            #         if (p not in keeppaths) or (not os.path.isfile(p)):
            #             dictionary[key].remove(p)
            #             print("Removed path ", p)
            # if len(dictionary[key]) == 0:
            #     dictionary.pop(key)
            #     print("Removed hash ", key)
            # return

        with ju.RotatingHandler("Test", basepath="databases", readonly=False, default=default) as jdb:
            with Spool(1) as spool:
                for key in list(jdb.keys()):
                    spool.enqueue(_pruneKey, (jdb, key,))


if __name__ == '__main__':
    TestData().test_fast()
    TestData().test_slow()
    TestData().test_purge()
