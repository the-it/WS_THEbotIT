# pylint: disable=protected-access,no-self-use
from unittest import mock
from unittest.mock import call

from testfixtures import compare

from service.ws_re.register.printer import ReRegisterPrinter
from service.ws_re.register.test_base import BaseTestRegister, copy_tst_data


class TestReRegisterPrinter(BaseTestRegister):
    def setUp(self):
        super().setUp()
        copy_tst_data("I_1_alpha", "I_1")
        copy_tst_data("III_1_alpha", "III_1")

    def test_print_alphabetic(self):
        with mock.patch("service.ws_re.register.printer.Page") as page_mock:
            printer = ReRegisterPrinter()
            printer._print_volume()
            compare(2, len(page_mock.call_args_list))
            compare(call(None, 'Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/I,1'),
                    page_mock.call_args_list[0])
            compare(call(None, 'Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/III,1'),
                    page_mock.call_args_list[1])

    def test_print_volume(self):
        with mock.patch("service.ws_re.register.printer.Page") as page_mock:
            printer = ReRegisterPrinter()
            printer._print_alphabetic()
            compare(44, len(page_mock.call_args_list))
            compare(call(None, 'Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/a'),
                    page_mock.call_args_list[0])
            compare(call(None, 'Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/ak'),
                    page_mock.call_args_list[1])
            compare(call(None, 'Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/z'),
                    page_mock.call_args_list[43])

    def test_print_author(self):
        with mock.patch("service.ws_re.register.printer.Page") as page_mock:
            printer = ReRegisterPrinter()
            printer.LEMMA_AUTHOR_SIZE = 3
            printer._print_author()
            compare(3, len(page_mock.call_args_list))
            compare(call(None, 'Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/Herman Abel'),
                    page_mock.call_args_list[0])
            compare(call(None, 'Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/Abert'),
                    page_mock.call_args_list[1])
            compare(
                call(None, 'Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/Autorenübersicht'),
                page_mock.call_args_list[2])

    def test_overview_line(self):
        printer = ReRegisterPrinter()
        register = next(printer.registers.author)
        compare("|-\n"
                "|data-sort-value=\"Abel, Herman\""
                "|[[Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/Herman Abel|Herman Abel]]\n"
                "|data-sort-value=\"0004\"|4",
                printer._create_overview_line(register, True))
        compare("|-\n"
                "|data-sort-value=\"Abel, Herman\"|Herman Abel\n"
                "|data-sort-value=\"0004\"|4",
                printer._create_overview_line(register, False))

    def test_task(self):
        printer = ReRegisterPrinter()
        volume_mock: mock.Mock = mock.Mock()
        alphabetic_mock = mock.Mock()
        author_mock = mock.Mock()
        printer._print_volume = volume_mock
        printer._print_alphabetic = alphabetic_mock
        printer._print_author = author_mock
        printer.task()
        self.assertTrue(volume_mock.called)
        self.assertTrue(alphabetic_mock.called)
        self.assertTrue(author_mock.called)
