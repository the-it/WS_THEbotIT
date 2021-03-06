from testfixtures import LogCapture, compare

from service.ws_re.scanner.tasks.keine_schoepfungshoehe import KSCHTask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage


class TestKSCHTask(TaskTestCase):
    def test_process(self):
        self.text_mock.return_value = """pre_text{{REDaten
}}
{{RE keine Schöpfungshöhe|1950}}
text
{{REAutor|Autor.}}
more text"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = KSCHTask(None, self.logger)
            compare({"success": True, "changed": True}, task.run(re_page))
            compare("1950", re_page[1]["TODESJAHR"].value)
            compare(True, re_page[1]["KEINE_SCHÖPFUNGSHÖHE"].value)
            compare("text", re_page[1].text)

    def test_process_varing_template(self):
        self.text_mock.return_value = """{{REDaten
}}
{{RE keine Schöpfungshöhe|tada}}
text
{{REAutor|Autor.}}"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = KSCHTask(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare("", re_page[0]["TODESJAHR"].value)
            compare(False, re_page[0]["KEINE_SCHÖPFUNGSHÖHE"].value)
            compare("{{RE keine Schöpfungshöhe|tada}}\ntext", re_page[0].text)

    def test_bug_underscore(self):
        self.text_mock.return_value = """{{REDaten
}}
{{RE_keine_Schöpfungshöhe|1960}}
text
{{REAutor|Autor.}}"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = KSCHTask(None, self.logger)
            compare({"success": True, "changed": True}, task.run(re_page))
            compare("1960", re_page[0]["TODESJAHR"].value)
            compare(True, re_page[0]["KEINE_SCHÖPFUNGSHÖHE"].value)
            compare("text", re_page[0].text)

    def test_bug_no_year_provided(self):
        self.text_mock.return_value = """{{REDaten
|BAND=VI A,1
|KEINE_SCHÖPFUNGSHÖHE=OFF
|TODESJAHR=
|GEBURTSJAHR=
}}
{{RE keine Schöpfungshöhe}}
blub
{{REAutor|E. Bernert.}}"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = KSCHTask(None, self.logger)
            compare({"success": True, "changed": True}, task.run(re_page))
            compare("1905", re_page[0]["TODESJAHR"].value)
            compare(True, re_page[0]["KEINE_SCHÖPFUNGSHÖHE"].value)
            compare("blub", re_page[0].text)
