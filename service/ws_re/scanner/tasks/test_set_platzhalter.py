from testfixtures import compare

from service.ws_re.scanner.tasks.set_platzhalter import SEPLTask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage


class TestSEPLTask(TaskTestCase):
    def test_get_pd_death(self):
        task = SEPLTask(None, self.logger)
        self.page_mock.text = """{{REDaten
|BAND=XII,1
|KORREKTURSTAND=
}}
something
{{REAutor|OFF}}"""
        re_page = RePage(self.page_mock)
        compare({'success': True, 'changed': True}, task.run(re_page))
        compare("Platzhalter", re_page.first_article["KORREKTURSTAND"].value)
