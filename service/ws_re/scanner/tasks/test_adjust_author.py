# pylint: disable=no-self-use
from unittest import TestCase

from ddt import ddt, file_data
from testfixtures import compare, LogCapture

from service.ws_re.scanner.tasks.adjust_author import ADAUTask, adjust_author, get_author_mapping
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage


@ddt
class TestAdjustAuthor(TestCase):
    @staticmethod
    def test_get_author_mapping():
        mapping = get_author_mapping()
        compare("Stein.", mapping["Arthur Stein"])
        compare("A.W.", mapping["Albert Wünsch"])
        compare("A. E. Gordon.", mapping["Arthur Ernest Gordon"])

    @file_data("test_data/test_adjust_author.yml")
    def test_adjust_author(self, given, expect):
        mapping = get_author_mapping()
        compare(expect, adjust_author(given, mapping))


class TestADAUTask(TaskTestCase):
    def test_adjust_simple_author(self):
        self.page_mock.text = """{{REDaten
|BAND=I,1
|KORREKTURSTAND=unvollständig
}}
test
{{REAutor|Arthur Stein}}"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = ADAUTask(None, self.logger)
            compare({"success": True, "changed": True}, task.run(re_page))
        compare("Stein.", re_page[0].author.short_string)

    def test_adjust_complex_author(self):
        self.page_mock.text = """{{REDaten
|BAND=I,1
|KORREKTURSTAND=unvollständig
}}
test
{{REAutor|Alfred Nagl}}"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = ADAUTask(None, self.logger)
            compare({"success": True, "changed": True}, task.run(re_page))
        compare("Nagl.", re_page[0].author.short_string)
        compare("I,1", re_page[0].author.issue)

    def test_skip_if_not_unvollstaendig(self):
        self.page_mock.text = """{{REDaten
|BAND=I,1
|KORREKTURSTAND=fertig
}}
test
{{REAutor|Arthur Stein}}"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = ADAUTask(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
        compare("Arthur Stein", re_page[0].author.short_string)

    def test_no_change_for_unknown_author(self):
        self.page_mock.text = """{{REDaten
|BAND=I,1
|KORREKTURSTAND=unvollständig
}}
test
{{REAutor|Fantasy Author}}"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = ADAUTask(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
