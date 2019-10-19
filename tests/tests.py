import pytest
import os

from snip import *

print('good day and welcome to tests')


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

    def test_writeJson(self):
        os.makedirs("tests", exist_ok=True)
        data.writeJsonToCsv([
            {
                "Column 1": "Item 1 Value 1",
                "Column 2": "Item 1 Value 2",
            },
            {
                "Column 1": "Item 2 Value 1",
                "Column 2": "Item 2 Value 2",
            }
        ], "tests/table_simple.csv")

        data.writeJsonToCsv([
            {
                "Column 1": 1,
                "Column 2": [2, 3],
            },
            {
                "Column 1": 4,
                "Column 2": [5, 6],
            }
        ], "tests/table_datatypes.csv")

        data.writeJsonToCsv([
            {
                "Column 1": 1,
                "Column 2": {
                    "A": "a",
                    "B": "b"
                },
            },
            {
                "Column 1": 4,
                "Column 2": {
                    "A": "c",
                    "B": "d"
                },
            }
        ], "tests/table_nested.csv")

        data.writeJsonToCsv([
            {
                "Column 1": 1,
                "Column 2": {
                    "A": "a",
                    "B": "b"
                },
            },
            {
                "Column 3": 4,
                "Column 4": {
                    "A": "c",
                    "B": "d"
                },
            }
        ], "tests/table_mismatch.csv")


class TestNest(object):

    def test_basic(self):
        n = nest.Nest()
        print(n)

