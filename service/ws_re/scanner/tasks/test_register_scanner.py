# pylint: disable=protected-access
from unittest import mock

import pywikibot
from ddt import file_data, ddt
from testfixtures import compare, LogCapture, StringComparison

from service.ws_re.register.repo import DataRepo
from service.ws_re.register.test_base import clear_tst_path, copy_tst_data
from service.ws_re.scanner.tasks.register_scanner import SCANTask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage
from tools.test import real_wiki_test


@ddt
class TestSCANTask(TaskTestCase):
    def setUp(self):
        super().setUp()
        copy_tst_data("I_1_base", "I_1")
        copy_tst_data("authors", "authors")
        copy_tst_data("authors_mapping", "authors_mapping")
        self.task = SCANTask(None, self.logger)

    @classmethod
    def setUpClass(cls):
        DataRepo.mock_data(True)
        clear_tst_path()

    @classmethod
    def tearDownClass(cls):
        clear_tst_path(renew_path=False)
        DataRepo.mock_data(False)

    def test_fetch_wikipedia_wikisource_link(self):
        self.page_mock.text = """{{REDaten
|BAND=I,1
|WP=Lemma
|WS=WsLemma
}}
text.
{{REAutor|OFF}}"""
        article_list = RePage(self.page_mock).splitted_article_list[0]
        compare(({"wp_link": "w:de:Lemma"}, []), self.task._fetch_wp_link(article_list))
        compare(({"ws_link": "s:de:WsLemma"}, []), self.task._fetch_ws_link(article_list))

    def test_fetch_wikipedia_link_no_link(self):
        with mock.patch("service.ws_re.scanner.tasks.register_scanner.SCANTask._get_link_from_wd",
                        mock.Mock(return_value=None)):
            self.page_mock.text = """{{REDaten
|BAND=I,1
}}
text.
{{REAutor|OFF}}"""
            re_page = RePage(self.page_mock)
            self.task.re_page = re_page
            article_list = re_page.splitted_article_list[0]
            compare(({}, ["wp_link"]), self.task._fetch_wp_link(article_list))
            compare(({}, ["ws_link"]), self.task._fetch_ws_link(article_list))

    def test_sortkey(self):
        self.page_mock.text = """{{REDaten
|BAND=I,1
|SORTIERUNG=Abalas limen
}}
text.
{{REAutor|OFF}}
{{REDaten
|BAND=S I
|SORTIERUNG=
}}
text.
{{REAutor|OFF}}"""
        re_page = RePage(self.page_mock)
        self.task.re_page = re_page
        compare(({"sort_key": "Abalas limen"}, []), self.task._fetch_sort_key(re_page.splitted_article_list[1]))

        self.page_mock.text = """{{REDaten
|BAND=I,1
}}
text.
{{REAutor|OFF}}"""
        re_page = RePage(self.page_mock)
        self.task.re_page = re_page
        compare(({}, ["sort_key"]), self.task._fetch_sort_key(re_page.splitted_article_list[0]))

    def test_lemma(self):
        self.page_mock.title_str = "RE:Aal"
        self.page_mock.text = """{{REDaten
|BAND=I,1
}}
text.
{{REAutor|OFF}}"""
        re_page = RePage(self.page_mock)
        article_list = re_page.splitted_article_list[0]
        task = SCANTask(None, self.logger)
        task.re_page = re_page
        compare(({"lemma": "Aal"}, []), task._fetch_lemma(article_list))

    @file_data("test_data/register_scanner/test_proof_read.yml")
    def test_proof_read(self, text, result):
        self.page_mock.title_str = "RE:Aal"
        self.page_mock.text = text
        re_page = RePage(self.page_mock)
        article_list = re_page.splitted_article_list[0]
        task = SCANTask(None, self.logger)
        task.re_page = re_page
        compare(result, task._fetch_proof_read(article_list))

    @file_data("test_data/register_scanner/test_redirect.yml")
    def test_redirect(self, text, result):
        task = SCANTask(None, self.logger)
        self.page_mock.text = text
        article_list = RePage(self.page_mock).splitted_article_list[0]
        compare(result, task._fetch_redirect(article_list))

    @file_data("test_data/register_scanner/test_previous.yml")
    def test_previous(self, text, result):
        self.page_mock.text = text
        article_list = RePage(self.page_mock).splitted_article_list[0]
        compare(result, SCANTask._fetch_previous(article_list))

    @file_data("test_data/register_scanner/test_next.yml")
    def test_next(self, text, result):
        self.page_mock.text = text
        article_list = RePage(self.page_mock).splitted_article_list[0]
        compare(result, SCANTask._fetch_next(article_list))

    @file_data("test_data/register_scanner/test_short_description.yml")
    def test_short_description(self, text, test_number, result):
        self.page_mock.text = text
        re_page = RePage(self.page_mock)
        self.task.re_page = re_page
        compare(result, self.task._fetch_short_description(re_page.splitted_article_list[test_number]))

    @file_data("test_data/register_scanner/test_no_creative_height.yml")
    def test_no_creative_height(self, text, result):
        self.page_mock.text = text
        article_list = RePage(self.page_mock).splitted_article_list[0]
        compare(result, SCANTask._fetch_no_creative_height(article_list))

    @file_data("test_data/register_scanner/test_pages_simple.yml")
    def test_pages(self, text, expect):
        task = SCANTask(None, self.logger)
        self.page_mock.title_str = "RE:Aal"
        self.page_mock.text = text
        re_page = RePage(self.page_mock)
        task.re_page = re_page
        article_list = re_page.splitted_article_list[0]
        compare(expect, task._fetch_pages(article_list))

    @file_data("test_data/register_scanner/test_pages_complex.yml")
    def test_pages_complex(self, text, expect):
        with LogCapture():
            task = SCANTask(None, self.logger)
            self.page_mock.title_str = "RE:Aal"
            self.page_mock.text = text
            re_page = RePage(self.page_mock)
            task.re_page = re_page
            article_list = re_page.splitted_article_list[0]
            compare(expect, task._fetch_pages(article_list))

    def test_fetch_from_properties(self):
        with LogCapture():
            self.page_mock.title_str = "RE:Aal"
            self.page_mock.text = """{{REDaten
|BAND=I,1
|VORGÄNGER=Lemma Previous
|NACHFOLGER=Lemma Next
|WP=Aal_wp_link
|WS=Aal_ws_link
|SORTIERUNG=Aal
|VERWEIS=ON
|KORREKTURSTAND=korrigiert
|KURZTEXT=Short Description
|KEINE_SCHÖPFUNGSHÖHE=ON
}}
text.
{{REAutor|OFF}}"""
            task = SCANTask(None, self.logger)
            task.re_page = RePage(self.page_mock)
            task._process_from_article_list()
            post_lemma_dict = task.registers["I,1"].get_lemma_by_name("Aal").to_dict()
            compare("w:de:Aal_wp_link", post_lemma_dict["wp_link"])
            compare("s:de:Aal_ws_link", post_lemma_dict["ws_link"])
            compare("Aal", post_lemma_dict["sort_key"])
            compare(2, post_lemma_dict["proof_read"])
            compare(True, post_lemma_dict["redirect"])
            compare("Lemma Previous", post_lemma_dict["previous"])
            compare("Lemma Next", post_lemma_dict["next"])
            compare("Short Description", post_lemma_dict["short_description"])
            compare(True, post_lemma_dict["no_creative_height"])

    def test_fetch_from_properties_self_append(self):
        with LogCapture():
            copy_tst_data("I_1_self_append", "I_1")
            self.page_mock.title_str = "RE:Aal"
            self.page_mock.text = """{{REDaten
|BAND=I,1
|VORGÄNGER=Something
|NACHFOLGER=Dummy-End
|SORTIERUNG=Aal
|SPALTE_START=5
|SPALTE_END=6
}}
text Hauptartikel.
{{REAutor|Abel.}}
{{REDaten
|BAND=I,1
|VORGÄNGER=Dummy-Start
|NACHFOLGER=Aarassos
|VERWEIS=ON
|WP=Aal_wp_link
|WS=Aal_ws_link
|SPALTE_START=1
|SPALTE_END=4
}}
text Verweis, aber früher im Band abgedruckt.
{{REAutor|OFF}}
"""
            task = SCANTask(None, self.logger)
            task.re_page = RePage(self.page_mock)
            task._process_from_article_list()
            post_lemma = task.registers["I,1"].get_lemma_by_name("Aal")
            post_lemma_dict = post_lemma.to_dict()
            compare("w:de:Aal_wp_link", post_lemma_dict["wp_link"])
            compare("s:de:Aal_ws_link", post_lemma_dict["ws_link"])
            compare("Aal", post_lemma_dict["sort_key"])
            compare(True, post_lemma_dict["redirect"])
            compare("Dummy-Start", post_lemma_dict["previous"])
            compare("Aarassos", post_lemma_dict["next"])
            post_lemma_append = task.registers["I,1"].get_lemma_by_name("Aal", self_supplement=True)
            compare("Something", post_lemma_append.to_dict()["previous"])
            compare("Dummy-End", post_lemma_append.to_dict()["next"])

    def test_fetch_from_properties_lemma_not_found(self):
        self.page_mock.title_str = "RE:Aas"
        self.page_mock.text = """{{REDaten
|BAND=I,1
|WP=Aal_wp_link
|WS=Aal_ws_link
}}
text.
{{REAutor|OFF}}"""
        task = SCANTask(None, self.logger)
        task.re_page = RePage(self.page_mock)
        with LogCapture() as log_catcher:
            task._process_from_article_list()
            log_catcher.check(mock.ANY, ("Test", "ERROR",
                                         StringComparison("No available Lemma in Registers for issue I,1 "
                                                          ".* Reason is:.*")))

    @real_wiki_test
    def test_get_wd_sitelink(self):
        WS_WIKI = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")
        self.task.re_page = RePage(pywikibot.Page(WS_WIKI, "RE:Demetrios 79"))
        compare(({'wp_link': 'w:en:Demetrius the Chronographer'}, []),
                self.task._fetch_wp_link(self.task.re_page.splitted_article_list[0]))
        compare(({'ws_link': 's:de:Apokryphen/Demetrius der Chronograph'}, []),
                self.task._fetch_ws_link(self.task.re_page.splitted_article_list[0]))
        compare(({'wd_link': 'd:Q3705296'}, []),
                self.task._fetch_wd_link(self.task.re_page.splitted_article_list[0]))
