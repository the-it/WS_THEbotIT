from ddt import ddt, file_data
import responses
from testfixtures import LogCapture
from unittest import TestCase, skip
import unittest.mock as mock
from unittest.mock import patch

__all__ = ["LogCapture", "TestCase",
           "ddt", "file_data", "is_subtuple", "mock", "patch", "responses", "skip"]


def is_subtuple(subtuple: tuple, supertuple: tuple) -> bool:
    try:
        old_index = supertuple.index(subtuple[0])
    except ValueError:
        return False
    for member in subtuple[1:]:
        try:
            index = supertuple.index(member)
        except ValueError:
            return False
        if not index == old_index + 1:
            return False
        old_index = index
    return True
