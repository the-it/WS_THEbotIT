from unittest import TestCase

from testfixtures import compare

from service.ws_re.scanner.tasks.correct_pd_dates import COPDTask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage


class TestCOPDTask(TaskTestCase):
    def test_remove_date(self):
        self.page_mock.text = """{{REDaten
|BAND=XII,1
|KEINE_SCHÖPFUNGSHÖHE=ON
|TODESJAHR=
|GEBURTSJAHR=1882
}}
something
{{REAutor|Obst.}}"""
        self.page_mock.title_str = "Re:Labax"
        re_page = RePage(self.page_mock)
        task = COPDTask(None, self.logger)
        compare({"success": True, "changed": True}, task.run(re_page))
        compare("", re_page.first_article["GEBURTSJAHR"].value)
        compare("", re_page.first_article["TODESJAHR"].value)
        compare(False, re_page.first_article["KEINE_SCHÖPFUNGSHÖHE"].value)
