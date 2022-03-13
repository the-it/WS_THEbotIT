from testfixtures import compare

from service.ws_re.scanner.tasks.add_short_description import KURZTask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage

class TestKURZTaskProcessSource(TaskTestCase):
    def test_1st(self):
        source_short_text = """{{REDaten
|BAND=S I
|KEINE_SCHÖPFUNGSHÖHE=ON
|TODESJAHR=1950
}}
bla
{{REAutor|Stein.}}"""
        re_page = RePage(self.page_mock)
        task = PDKSTask(None, self.logger)
        compare({"success": True, "changed": True}, task.run(re_page))
        compare("", re_page[0]["TODESJAHR"].value)
