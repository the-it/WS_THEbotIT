from testfixtures import compare

from service.ws_re.scanner.tasks.set_unvollstaendig import SEUVTask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage


class TestSEPLTask(TaskTestCase):
    def test_from_empty(self):
        task = SEUVTask(None, self.logger)
        self.page_mock.text = """{{REDaten
|BAND=XII,1
|KORREKTURSTAND=
}}
something
{{REAutor|OFF}}"""
        re_page = RePage(self.page_mock)
        compare({'success': True, 'changed': True}, task.run(re_page))
        compare("Unvollständig", re_page.first_article["KORREKTURSTAND"].value)
