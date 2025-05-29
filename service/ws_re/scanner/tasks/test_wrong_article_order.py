# pylint: disable=protected-access
from testfixtures import compare

from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.scanner.tasks.wrong_article_order import WAORTask
from service.ws_re.template.re_page import RePage

BASE_TASK_PYWIKIBOT_PAGE = "service.ws_re.scanner.tasks.base_task.pywikibot.Page"

class TestDEALTask(TaskTestCase):
    def test_only_one_article(self):
        self.page_mock.text = """{{REDaten
        }}
        {{REAutor|Autor.}}"""
        self.page_mock.title_str = "Re:Title1"
        re_page = RePage(self.page_mock)
        task = WAORTask(None, self.logger)
        compare({"success": True, "changed": False}, task.run(re_page))
        compare([], task.data)

    def test_first_article_no_verweis(self):
        self.page_mock.text = """{{REDaten
        |VERWEIS=OFF
        }}
        {{REAutor|Autor.}}
        {{REDaten
        |NACHTRAG=ON
        }}
        {{REAutor|Autor.}}"""
        self.page_mock.title_str = "Re:Title2"
        re_page = RePage(self.page_mock)
        task = WAORTask(None, self.logger)
        compare({"success": True, "changed": False}, task.run(re_page))
        compare([], task.data)

    def test_second_not_enough_content(self):
        self.page_mock.text = """{{REDaten
        |VERWEIS=ON
        }}
        {{REAutor|Autor.}}
        {{REDaten
        |NACHTRAG=ON
        }}
        01234567890123456789
        {{REAutor|Autor.}}"""
        self.page_mock.title_str = "Re:Title3"
        re_page = RePage(self.page_mock)
        task = WAORTask(None, self.logger)
        compare({"success": True, "changed": False}, task.run(re_page))
        compare([], task.data)

    def test_main_article_is_the_third_one(self):
        # first article is a VERWEIS, second article has not enough content
        self.page_mock.text = """{{REDaten
        |VERWEIS=ON
        }}
        {{REAutor|Autor.}}
        {{REDaten
        |NACHTRAG=ON
        }}
        01234567890123456789
        {{REAutor|Autor.}}
        {{REDaten
        |NACHTRAG=ON
        }}
        01234567890123456789
        01234567890123456789
        01234567890123456789
        01234567890123456789
        01234567890123456789
        01234567890123456789
        {{REAutor|Autor.}}"""
        self.page_mock.title_str = "Re:Title4"
        re_page = RePage(self.page_mock)
        task = WAORTask(None, self.logger)
        compare({"success": True, "changed": False}, task.run(re_page))
        compare(["Re:Title4"], task.data)
