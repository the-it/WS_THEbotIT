from testfixtures import compare

from service.ws_re.scanner.tasks.temp_obst import TOBSTask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage


class TestTOBSTask(TaskTestCase):
    def test_sets_flag_for_fertig(self):
        task = TOBSTask(None, self.logger)
        self.page_mock.text = """{{REDaten
|BAND=XII,1
|KORREKTURSTAND=Fertig
|KEINE_SCHÖPFUNGSHÖHE=OFF
}}
something
{{REAutor|Obst.}}"""
        re_page = RePage(self.page_mock)
        task.run(re_page)
        compare(True, re_page.first_article["KEINE_SCHÖPFUNGSHÖHE"].value)

    def test_sets_flag_for_korrigiert(self):
        task = TOBSTask(None, self.logger)
        self.page_mock.text = """{{REDaten
|BAND=XII,1
|KORREKTURSTAND=Korrigiert
|KEINE_SCHÖPFUNGSHÖHE=OFF
}}
something
{{REAutor|Obst.}}"""
        re_page = RePage(self.page_mock)
        task.run(re_page)
        compare(True, re_page.first_article["KEINE_SCHÖPFUNGSHÖHE"].value)

    def test_no_change_for_other_author(self):
        task = TOBSTask(None, self.logger)
        self.page_mock.text = """{{REDaten
|BAND=XII,1
|KORREKTURSTAND=Fertig
|KEINE_SCHÖPFUNGSHÖHE=OFF
}}
something
{{REAutor|OFF}}"""
        re_page = RePage(self.page_mock)
        task.run(re_page)
        compare(False, re_page.first_article["KEINE_SCHÖPFUNGSHÖHE"].value)

    def test_no_change_for_other_status(self):
        task = TOBSTask(None, self.logger)
        self.page_mock.text = """{{REDaten
|BAND=XII,1
|KORREKTURSTAND=Unvollständig
|KEINE_SCHÖPFUNGSHÖHE=OFF
}}
something
{{REAutor|Obst.}}"""
        re_page = RePage(self.page_mock)
        task.run(re_page)
        compare(False, re_page.first_article["KEINE_SCHÖPFUNGSHÖHE"].value)

    def test_wasnt_running(self):
        task = TOBSTask(None, self.logger)
        self.page_mock.text = """{{REDaten
|BAND=XII,1
|KORREKTURSTAND=korrigiert
|KEINE_SCHÖPFUNGSHÖHE=OFF
}}
something
{{REAutor|Obst.}}"""
        re_page = RePage(self.page_mock)
        task.run(re_page)
        compare(True, re_page.first_article["KEINE_SCHÖPFUNGSHÖHE"].value)
