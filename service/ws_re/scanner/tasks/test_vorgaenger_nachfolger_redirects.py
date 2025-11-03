# pylint: disable=protected-access
from pywikibot import Site
from testfixtures import compare

from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage
from service.ws_re.scanner.tasks.vorgaenger_nachfolger_redirects import VONATask
from tools.test import real_wiki_test


class TestVONATask(TaskTestCase):
    def setUp(self):
        super().setUp()
        WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
        self.task = VONATask(WS_WIKI, self.logger)

    @staticmethod
    def _base_text(vorgaenger: str = "", nachfolger: str = "") -> str:
        vg = f"|VORGÄNGER={vorgaenger}\n" if vorgaenger is not None else ""
        nf = f"|NACHFOLGER={nachfolger}\n" if nachfolger is not None else ""
        return """{{REDaten
|BAND=I,1
%s%s}}
text.
{{REAutor|OFF}}""" % (vg, nf)

    @real_wiki_test
    def test_no_redirect_no_change(self):
        self.page_mock.text = self._base_text("", "Ἀγράφου μετάλλου γραφή") + "something" + \
                              self._base_text("Ἀγραφίου γραφή", "Ἀγράφου μετάλλου γραφή")
        re_page = RePage(self.page_mock)
        self.task.re_page = re_page
        self.task.task()
        # text unchanged
        compare("", re_page[0]["VORGÄNGER"].value)
        compare("Ἀγράφου μετάλλου γραφή", re_page[0]["NACHFOLGER"].value)
        compare("Ἀγραφίου γραφή", re_page[2]["VORGÄNGER"].value)
        compare("Ἀγράφου μετάλλου γραφή", re_page[2]["NACHFOLGER"].value)

    @real_wiki_test
    def test_both_redirect(self):
        self.page_mock.text = self._base_text("Agraphiu graphe", "Agraphu metallu graphe")
        re_page = RePage(self.page_mock)
        self.task.re_page = re_page
        self.task.task()
        # text unchanged
        compare("Ἀγραφίου γραφή", re_page[0]["VORGÄNGER"].value)
        compare("Ἀγράφου μετάλλου γραφή", re_page[0]["NACHFOLGER"].value)
