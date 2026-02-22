from testfixtures import compare

from service.ws_re.scanner.tasks.correct_korrekturstand import COKSTask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage


class TestCOKSTask(TaskTestCase):
    def test_platzhalter_to_unvollstaendig(self):
        task = COKSTask(None, self.logger)
        self.page_mock.text = """{{REDaten
|BAND=XII,1
|KORREKTURSTAND=Platzhalter
}}
something
{{REAutor|OFF}}"""
        re_page = RePage(self.page_mock)
        compare({'success': True, 'changed': True}, task.run(re_page))
        compare("unvollständig", re_page.first_article["KORREKTURSTAND"].value)

    def test_fertig_to_lowercase(self):
        task = COKSTask(None, self.logger)
        self.page_mock.text = """{{REDaten
|BAND=XII,1
|KORREKTURSTAND=Fertig
}}
something
{{REAutor|OFF}}"""
        re_page = RePage(self.page_mock)
        compare({'success': True, 'changed': True}, task.run(re_page))
        compare("fertig", re_page.first_article["KORREKTURSTAND"].value)

    def test_korrigiert_to_lowercase(self):
        task = COKSTask(None, self.logger)
        self.page_mock.text = """{{REDaten
|BAND=XII,1
|KORREKTURSTAND=Korrigiert
}}
something
{{REAutor|OFF}}"""
        re_page = RePage(self.page_mock)
        compare({'success': True, 'changed': True}, task.run(re_page))
        compare("korrigiert", re_page.first_article["KORREKTURSTAND"].value)

    def test_unkorrigiert_to_lowercase(self):
        task = COKSTask(None, self.logger)
        self.page_mock.text = """{{REDaten
|BAND=XII,1
|KORREKTURSTAND=Unkorrigiert
}}
something
{{REAutor|OFF}}"""
        re_page = RePage(self.page_mock)
        compare({'success': True, 'changed': True}, task.run(re_page))
        compare("unkorrigiert", re_page.first_article["KORREKTURSTAND"].value)

    def test_no_change_when_already_correct(self):
        task = COKSTask(None, self.logger)
        self.page_mock.text = """{{REDaten
|BAND=XII,1
|KORREKTURSTAND=fertig
}}
something
{{REAutor|OFF}}"""
        re_page = RePage(self.page_mock)
        compare({'success': True, 'changed': False}, task.run(re_page))
        compare("fertig", re_page.first_article["KORREKTURSTAND"].value)

    def test_unvollstaendig(self):
        task = COKSTask(None, self.logger)
        self.page_mock.text = """{{REDaten
|BAND=XII,1
|KORREKTURSTAND=Unvollständig
}}
something
{{REAutor|OFF}}"""
        re_page = RePage(self.page_mock)
        compare({'success': True, 'changed': False}, task.run(re_page))
        compare("unvollständig", re_page.first_article["KORREKTURSTAND"].value)

    def test_no_change_when_empty(self):
        task = COKSTask(None, self.logger)
        self.page_mock.text = """{{REDaten
|BAND=XII,1
|KORREKTURSTAND=
}}
something
{{REAutor|OFF}}"""
        re_page = RePage(self.page_mock)
        compare({'success': True, 'changed': False}, task.run(re_page))
        compare("", re_page.first_article["KORREKTURSTAND"].value)
