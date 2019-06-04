import pytest

from snip import *


class TestData(object):

    def test_chunk(self):
        it = [1, 2, 3, 4, 5]
        assert list(data.chunk(it, 0)) == []
        assert list(data.chunk(it, 3)) == [(1, 2, 3), (4, 5)]
        assert list(data.chunk(it, 5)) == [(1, 2, 3, 4, 5)]

        it = [1, 2, 3, 4, 5, 6]
        assert list(data.chunk(it, 3)) == [(1, 2, 3), (4, 5, 6)]

    def test_flatList(self):
        assert data.flatList([[1, 2], [3, 4]]) == [1, 2, 3, 4]



