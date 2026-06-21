from unittest import mock

from testfixtures import LogCapture, compare

from service.ws_re.scanner.tasks.add_issue_to_complex_author import AICATask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage

COMPLEX_MAPPING = {
    "Abel": {"*": "Herman Abel", "XVI,1": "Abel_XVI,1"},
    "Stein.": "Arthur Stein",
}


@mock.patch("service.ws_re.scanner.tasks.add_issue_to_complex_author.Authors")
class TestAICATask(TaskTestCase):
    def _build_task(self, authors_mock):
        authors_mock.return_value.authors_mapping = COMPLEX_MAPPING
        return AICATask(None, self.logger)

    def test_add_issue_for_complex_author(self, authors_mock):
        self.page_mock.text = """{{REDaten
|BAND=XVI,1
|KORREKTURSTAND=unvollständig
}}
test
{{REAutor|Abel}}"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = self._build_task(authors_mock)
            compare({"success": True, "changed": True}, task.run(re_page))
        compare("Abel", re_page[0].author.short_string)
        compare("XVI,1", re_page[0].author.issue)

    def test_no_change_for_simple_author(self, authors_mock):
        self.page_mock.text = """{{REDaten
|BAND=I,1
|KORREKTURSTAND=unvollständig
}}
test
{{REAutor|Stein.}}"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = self._build_task(authors_mock)
            compare({"success": True, "changed": False}, task.run(re_page))
        compare("", re_page[0].author.issue)

    def test_no_change_for_unknown_author(self, authors_mock):
        self.page_mock.text = """{{REDaten
|BAND=I,1
|KORREKTURSTAND=unvollständig
}}
test
{{REAutor|Fantasy Author}}"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = self._build_task(authors_mock)
            compare({"success": True, "changed": False}, task.run(re_page))

    def test_corrects_existing_issue_to_band(self, authors_mock):
        self.page_mock.text = """{{REDaten
|BAND=XVI,1
|KORREKTURSTAND=unvollständig
}}
test
{{REAutor|Abel|III,2}}"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = self._build_task(authors_mock)
            compare({"success": True, "changed": True}, task.run(re_page))
        compare("XVI,1", re_page[0].author.issue)
