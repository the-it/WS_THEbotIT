# pylint: disable=protected-access, no-self-use
from unittest import TestCase, mock

from testfixtures import compare

from tools.utils import save_if_changed


class TestUtils(TestCase):
    def test_save_if_changed_positive(self):
        page_mock = mock.Mock()
        text_mock = mock.PropertyMock()
        type(page_mock).text = text_mock
        text_mock.return_value = "2"
        save_if_changed(page_mock, "1", "changed")
        compare(mock.call.save("changed", botflag=True), page_mock.mock_calls[0])

    def test_save_if_changed_negativ(self):
        page_mock = mock.Mock()
        text_mock = mock.PropertyMock()
        type(page_mock).text = text_mock
        text_mock.return_value = "1"
        save_if_changed(page_mock, "1", "changed")
        compare(0, len(page_mock.mock_calls))

        save_if_changed(page_mock, "1 ", "changed")
        compare(0, len(page_mock.mock_calls))
