# pylint: disable=protected-access
from testfixtures import compare

from service.ws_re.scanner.tasks.nachtrag_ueberschrift import NAUETask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage


class TestNAUETask(TaskTestCase):
    def test_single_article_correct(self):
        self.page_mock.text = """{{REDaten
|NACHTRAG=OFF
|ÜBERSCHRIFT=OFF
}}
text
{{REAutor|Autor.}}"""
        re_page = RePage(self.page_mock)
        task = NAUETask(None, self.logger)
        compare({"success": True, "changed": False}, task.run(re_page))

    def test_single_article_gets_corrected(self):
        self.page_mock.text = """{{REDaten
|NACHTRAG=ON
|ÜBERSCHRIFT=ON
}}
text
{{REAutor|Autor.}}"""
        re_page = RePage(self.page_mock)
        task = NAUETask(None, self.logger)
        compare({"success": True, "changed": True}, task.run(re_page))
        article = re_page.splitted_article_list[0].daten
        compare(False, article["NACHTRAG"].value)
        compare(False, article["ÜBERSCHRIFT"].value)

    def test_two_articles_correct(self):
        self.page_mock.text = """{{REDaten
}}
text
{{REAutor|Autor.}}
{{REDaten
|NACHTRAG=ON
|ÜBERSCHRIFT=ON
}}
text
{{REAutor|Autor.}}"""
        re_page = RePage(self.page_mock)
        task = NAUETask(None, self.logger)
        compare({"success": True, "changed": False}, task.run(re_page))

    def test_second_article_gets_corrected(self):
        self.page_mock.text = """{{REDaten
}}
text
{{REAutor|Autor.}}
{{REDaten
|NACHTRAG=OFF
|ÜBERSCHRIFT=OFF
}}
text
{{REAutor|Autor.}}"""
        re_page = RePage(self.page_mock)
        task = NAUETask(None, self.logger)
        compare({"success": True, "changed": True}, task.run(re_page))
        article = re_page.splitted_article_list[1].daten
        compare(True, article["NACHTRAG"].value)
        compare(True, article["ÜBERSCHRIFT"].value)

    def test_three_articles_correct(self):
        self.page_mock.text = """{{REDaten
}}
text
{{REAutor|Autor.}}
{{REDaten
|NACHTRAG=ON
|ÜBERSCHRIFT=ON
}}
text
{{REAutor|Autor.}}
{{REDaten
|NACHTRAG=ON
|ÜBERSCHRIFT=OFF
}}
text
{{REAutor|Autor.}}"""
        re_page = RePage(self.page_mock)
        task = NAUETask(None, self.logger)
        compare({"success": True, "changed": False}, task.run(re_page))

    def test_third_article_gets_corrected(self):
        self.page_mock.text = """{{REDaten
}}
text
{{REAutor|Autor.}}
{{REDaten
|NACHTRAG=ON
|ÜBERSCHRIFT=ON
}}
text
{{REAutor|Autor.}}
{{REDaten
|NACHTRAG=OFF
|ÜBERSCHRIFT=ON
}}
text
{{REAutor|Autor.}}"""
        re_page = RePage(self.page_mock)
        task = NAUETask(None, self.logger)
        compare({"success": True, "changed": True}, task.run(re_page))
        article = re_page.splitted_article_list[2].daten
        compare(True, article["NACHTRAG"].value)
        compare(False, article["ÜBERSCHRIFT"].value)
        self.assertTrue("|NACHTRAG=ON\n|ÜBERSCHRIFT=OFF" in str(re_page))

    def test_re_abschnitt_is_ignored(self):
        self.page_mock.text = """{{REDaten
}}
text
{{REAutor|Autor.}}
{{REAbschnitt}}
text
{{REAutor|Autor.}}
{{REDaten
|NACHTRAG=ON
|ÜBERSCHRIFT=ON
}}
text
{{REAutor|Autor.}}"""
        re_page = RePage(self.page_mock)
        task = NAUETask(None, self.logger)
        compare({"success": True, "changed": False}, task.run(re_page))
