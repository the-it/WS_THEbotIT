from testfixtures import LogCapture, compare

from service.ws_re.scanner.tasks.gemeinfrei_2021 import GF21Task
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage


class TestGF21Task(TaskTestCase):
    def test_process_willrich(self):
        self.text_mock.return_value = """{{REDaten
|BAND=S I
|KEINE_SCHÖPFUNGSHÖHE=ON
|TODESJAHR=1950
}}
bla
{{REAutor|Willrich.}}"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = GF21Task(None, self.logger)
            compare({"success": True, "changed": True}, task.run(re_page))
            compare("", re_page[0]["TODESJAHR"].value)

    def test_process_stein(self):
        self.text_mock.return_value = """{{REDaten
|BAND=S I
|KEINE_SCHÖPFUNGSHÖHE=ON
|TODESJAHR=1950
}}
bla
{{REAutor|Stein.}}"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = GF21Task(None, self.logger)
            compare({"success": True, "changed": True}, task.run(re_page))
            compare("", re_page[0]["TODESJAHR"].value)

    def test_process_capps(self):
        self.text_mock.return_value = """{{REDaten
|BAND=S I
|KEINE_SCHÖPFUNGSHÖHE=ON
|TODESJAHR=1950
}}
bla
{{REAutor|Capps.}}"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = GF21Task(None, self.logger)
            compare({"success": True, "changed": True}, task.run(re_page))
            compare("", re_page[0]["TODESJAHR"].value)

    def test_process_hug(self):
        self.text_mock.return_value = """{{REDaten
|BAND=S I
|KEINE_SCHÖPFUNGSHÖHE=ON
|TODESJAHR=1950
}}
bla
{{REAutor|Hug.}}"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = GF21Task(None, self.logger)
            compare({"success": True, "changed": True}, task.run(re_page))
            compare("", re_page[0]["TODESJAHR"].value)

    def test_process_do_nothing(self):
        self.text_mock.return_value = """{{REDaten
|BAND=S I
|KEINE_SCHÖPFUNGSHÖHE=ON
|TODESJAHR=
}}
bla
{{REAutor|Hug.}}"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = GF21Task(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare("", re_page[0]["TODESJAHR"].value)

    def test_process_do_nothing_schoepfungshoehe(self):
        self.text_mock.return_value = """{{REDaten
|BAND=S I
|KEINE_SCHÖPFUNGSHÖHE=OFF
|TODESJAHR=1950
}}
bla
{{REAutor|Hug.}}"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = GF21Task(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare("1950", re_page[0]["TODESJAHR"].value)
