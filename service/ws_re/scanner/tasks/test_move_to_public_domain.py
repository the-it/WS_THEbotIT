from freezegun import freeze_time
from testfixtures import compare

from service.ws_re.scanner.tasks.move_to_public_domain import PDKSTask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage

@freeze_time("2021-01-01")
class TestCOPDTask(TaskTestCase):
    def test_process_newly_public_domain_tj(self):
        """
        article is in public domain since this day and has no height of creation. Defined by death year.
        Expectation: article changed
        """
        self.page_mock.text = """{{REDaten
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

    def test_process_newly_public_domain_gj(self):
        """
        article is in public domain since this day and has no height of creation. Defined by birth year.
        Expectation: article changed
        """
        self.page_mock.text = """{{REDaten
|BAND=S I
|KEINE_SCHÖPFUNGSHÖHE=ON
|GEBURTSJAHR=1870
}}
bla
{{REAutor|Stein.}}"""
        re_page = RePage(self.page_mock)
        task = PDKSTask(None, self.logger)
        compare({"success": True, "changed": True}, task.run(re_page))
        compare("", re_page[0]["GEBURTSJAHR"].value)

    def test_process_newly_public_domain_tj_not_yet(self):
        """
        article is not in public domain since and has no height of creation. Defined by death year.
        Expectation: article not changed
        """
        self.page_mock.text = """{{REDaten
|BAND=S I
|KEINE_SCHÖPFUNGSHÖHE=ON
|TODESJAHR=1951
}}
bla
{{REAutor|Stein.}}"""
        re_page = RePage(self.page_mock)
        task = PDKSTask(None, self.logger)
        compare({"success": True, "changed": False}, task.run(re_page))
        compare("1951", re_page[0]["TODESJAHR"].value)

    def test_process_newly_public_domain_gj_not_yet(self):
        """
        article is not in public domain since and has no height of creation. Defined by birth year.
        Expectation: article not changed
        """
        self.page_mock.text = """{{REDaten
|BAND=S I
|KEINE_SCHÖPFUNGSHÖHE=ON
|GEBURTSJAHR=1871
}}
bla
{{REAutor|Stein.}}"""
        re_page = RePage(self.page_mock)
        task = PDKSTask(None, self.logger)
        compare({"success": True, "changed": False}, task.run(re_page))
        compare("1871", re_page[0]["GEBURTSJAHR"].value)

    def test_process_newly_public_domain_height_of_creation(self):
        """
        article is in public domain since but has height of creation.
        Expectation: article not changed
        """
        self.page_mock.text = """{{REDaten
|BAND=S I
|KEINE_SCHÖPFUNGSHÖHE=OFF
|TODESJAHR=1950
}}
bla
{{REAutor|Stein.}}"""
        re_page = RePage(self.page_mock)
        task = PDKSTask(None, self.logger)
        compare({"success": True, "changed": False}, task.run(re_page))
        compare("1950", re_page[0]["TODESJAHR"].value)
