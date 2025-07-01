from freezegun import freeze_time
from testfixtures import compare

from service.ws_re.scanner.tasks.correct_pd_dates import COPDTask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage


@freeze_time("2025-01-01")
class TestCOPDTask(TaskTestCase):
    def setUp(self):
        super().setUp()
        self.task = COPDTask(None, self.logger)
        pass

    def test_get_pd_death(self):
        self.page_mock.text = """{{REDaten
|BAND=XII,1
|KEINE_SCHÖPFUNGSHÖHE=ON
|TODESJAHR=
|GEBURTSJAHR=1882
}}
something
{{REAutor|Obst.}}"""
        re_page = RePage(self.page_mock)
        article_list = re_page.splitted_article_list[0]
        compare({"birth": None, "death": 1944, "pd": 2015}, self.task.get_max_pd_year(article_list))

    def test_get_pd_birth(self):
        self.page_mock.text = """{{REDaten
|BAND=XII,1
|KEINE_SCHÖPFUNGSHÖHE=ON
|TODESJAHR=
|GEBURTSJAHR=
}}
something
{{REAutor|Werner Eck.}}"""
        re_page = RePage(self.page_mock)
        article_list = re_page.splitted_article_list[0]
        compare({"birth": 1939, "death": None, "pd": 2090}, self.task.get_max_pd_year(article_list))
