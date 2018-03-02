import responses
from testfixtures import LogCapture
from unittest import TestCase
import unittest.mock as mock
from unittest.mock import patch

__all__ = ["LogCapture", "PropertyInstanceMock", "TestCase", "mock", "patch", "responses"]


class PropertyInstanceMock(mock.PropertyMock):
    """ Like PropertyMock, but records the instance that was called.
    """

    def __get__(self, obj, obj_type):
        return self(obj)

    def __set__(self, obj, val):
        self(obj, val)
