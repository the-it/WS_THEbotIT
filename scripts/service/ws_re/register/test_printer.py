# pylint: disable=protected-access,no-self-use
from unittest import mock
from unittest.mock import call

from testfixtures import compare

from scripts.service.ws_re.register.printer import ReRegisterPrinter
from scripts.service.ws_re.register.test_base import BaseTestRegister, copy_tst_data


class TestReRegisterPrinter(BaseTestRegister):
    def setUp(self):
        super().setUp()
        copy_tst_data("I_1_alpha", "I_1")
        copy_tst_data("III_1_alpha", "III_1")

    def test_print_alphabetic(self):
        with mock.patch("scripts.service.ws_re.register.printer.Page") as page_mock:
            printer = ReRegisterPrinter()
            printer._print_volume()
            compare(2, len(page_mock.call_args_list))
            compare(call(None, 'Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/I,1'),
                    page_mock.call_args_list[0])
            compare(call(None, 'Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/III,1'),
                    page_mock.call_args_list[1])

    def test_print_volume(self):
        with mock.patch("scripts.service.ws_re.register.printer.Page") as page_mock:
            printer = ReRegisterPrinter()
            printer._print_alphabetic()
            compare(44, len(page_mock.call_args_list))
            compare(call(None, 'Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/a'),
                    page_mock.call_args_list[0])
            compare(call(None, 'Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/ak'),
                    page_mock.call_args_list[1])
            compare(call(None, 'Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/z'),
                    page_mock.call_args_list[43])
