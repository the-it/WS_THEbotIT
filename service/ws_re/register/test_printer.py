# pylint: disable=protected-access,no-self-use
from datetime import datetime
from unittest import mock
from unittest.mock import call

from testfixtures import compare

from service.ws_re.register.printer import ReRegisterPrinter
from service.ws_re.register.test_base import BaseTestRegister, copy_tst_data
from tools.bots.cloud.test_base import TestCloudBase


class TestReRegisterPrinter(BaseTestRegister, TestCloudBase):
    @classmethod
    def setUpClass(cls):
        BaseTestRegister.setUpClass()
        TestCloudBase.setUpClass()

    @classmethod
    def tearDownClass(cls):
        BaseTestRegister.tearDownClass()
        TestCloudBase.tearDownClass()

    def setUp(self):
        BaseTestRegister.setUp(self)
        TestCloudBase.setUp(self)
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

    def test_print_short(self):
        with mock.patch("service.ws_re.register.printer.Page") as page_mock:
            printer = ReRegisterPrinter()
            printer._print_short()
            compare(50, len(page_mock.call_args_list))
            compare(call(None, 'Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/I kurz'),
                    page_mock.call_args_list[0])
            compare(call(None, 'Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/XI kurz'),
                    page_mock.call_args_list[10])
            compare(call(None, 'Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/XXI kurz'),
                    page_mock.call_args_list[20])
            compare(call(None, 'Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/VII A kurz'),
                    page_mock.call_args_list[30])
            compare(call(None, 'Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/S VII kurz'),
                    page_mock.call_args_list[40])
            compare(call(None, 'Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/R kurz'),
                    page_mock.call_args_list[49])

    def test_print_pd(self):
        with mock.patch("service.ws_re.register.printer.Page") as page_mock:
            printer = ReRegisterPrinter()
            printer._print_pd()
            current_year = datetime.now().year
            compare(10, len(page_mock.call_args_list))
            compare(call(None,
                         f'Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/'
                         f'PD {current_year - 5}'),
                    page_mock.call_args_list[0])
            compare(call(None,
                         f'Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/'
                         f'PD {current_year + 4}'),
                    page_mock.call_args_list[9])

    def test_print_author(self):
        with mock.patch("service.ws_re.register.printer.Page") as page_mock:
            printer = ReRegisterPrinter()
            printer._print_author()
            compare(4, len(page_mock.call_args_list))
            compare(call(None, 'Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/Herman Abel'),
                    page_mock.call_args_list[0])
            compare(call(None, 'Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/Abert'),
                    page_mock.call_args_list[1])
            compare(call(None, 'Paulys Realencyclopädie der classischen Altertumswissenschaft/'
                               'Register/William Abbott'),
                    page_mock.call_args_list[2])
            compare(
                call(None, 'Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/Autorenübersicht'),
                page_mock.call_args_list[3])

    def test_task(self):
        printer = ReRegisterPrinter()
        volume_mock: mock.Mock = mock.Mock()
        alphabetic_mock = mock.Mock()
        author_mock = mock.Mock()
        short_mock = mock.Mock()
        pd_mock = mock.Mock()
        printer._print_volume = volume_mock
        printer._print_alphabetic = alphabetic_mock
        printer._print_author = author_mock
        printer._print_short = short_mock
        printer._print_pd = pd_mock
        printer.task()
        self.assertTrue(volume_mock.called)
        self.assertTrue(alphabetic_mock.called)
        self.assertTrue(author_mock.called)
        self.assertTrue(short_mock.called)
        self.assertTrue(pd_mock.called)
