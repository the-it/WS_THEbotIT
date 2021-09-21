# pylint: disable=protected-access
from unittest import mock, skip

import pywikibot
from ddt import file_data, ddt
from git import Repo
from testfixtures import compare, LogCapture, StringComparison

from service.ws_re.register.authors import Authors
from service.ws_re.register._base import _REGISTER_PATH
from service.ws_re.register.register_types.volume import VolumeRegister
from service.ws_re.register.test_base import clear_tst_path, _TEST_REGISTER_PATH, \
    copy_tst_data
from service.ws_re.scanner.tasks.register_scanner import SCANTask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage


class TaskTestWithRegister(TaskTestCase):
    @classmethod
    def setUpClass(cls):
        clear_tst_path()
        Authors._REGISTER_PATH = _TEST_REGISTER_PATH
        VolumeRegister._REGISTER_PATH = _TEST_REGISTER_PATH

    @classmethod
    def tearDownClass(cls):
        Authors._REGISTER_PATH = _REGISTER_PATH
        VolumeRegister._REGISTER_PATH = _REGISTER_PATH
        clear_tst_path(renew_path=False)

@ddt
class TestSCANTask(TaskTestWithRegister):
    # pylint: disable=arguments-differ
    def setUp(self):
        super().setUp()  # pylint: disable=no-value-for-parameter
        copy_tst_data("I_1_base", "I_1")
        copy_tst_data("authors", "authors")
        copy_tst_data("authors_mapping", "authors_mapping")
        self.task = SCANTask(None, self.logger)

    def test_pushing_nothing_to_push(self):
        with mock.patch("service.ws_re.scanner.tasks.register_scanner.Repo",
                        mock.Mock(spec=Repo)) as repo_mock:
            repo_mock().index.diff.return_value = []
            self.task._push_changes()
            compare(3, len(repo_mock.mock_calls))
            compare(mock.call(search_parent_directories=True), repo_mock.mock_calls[1])
            compare("().index.diff", repo_mock.mock_calls[2][0])

    def test_pushing_changes(self):
        with LogCapture():
            with mock.patch("service.ws_re.scanner.tasks.register_scanner.Repo",
                            mock.Mock(spec=Repo)) as repo_mock:
                repo_mock().index.diff.return_value = ["Something has changed"]
                self.task._push_changes()
                compare(6, len(repo_mock.mock_calls))
                compare(mock.call(search_parent_directories=True), repo_mock.mock_calls[1])
                compare("().index.diff", repo_mock.mock_calls[2][0])
                compare("().git.add", repo_mock.mock_calls[3][0])
                compare(StringComparison(r".*/service/ws_re/register/data"), repo_mock.mock_calls[3][1][0])
                compare("().index.commit", repo_mock.mock_calls[4][0])
                compare(StringComparison(r"Updating the register at \d{6}_\d{6}"), repo_mock.mock_calls[4][1][0])
                compare("().git.push", repo_mock.mock_calls[5][0])

    def test_fetch_wikipedia_wikisource_link(self):
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
|WP=Lemma
|WS=WsLemma
}}
text.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({"wp_link": "w:de:Lemma"}, []), self.task._fetch_wp_link(article))
        compare(({"ws_link": "s:de:WsLemma"}, []), self.task._fetch_ws_link(article))

    def test_fetch_wikipedia_link_no_link(self):
        with mock.patch("service.ws_re.scanner.tasks.register_scanner.SCANTask._get_link_from_wd",
                        mock.Mock(return_value=None)):
            self.text_mock.return_value = """{{REDaten
|BAND=I,1
}}
text.
{{REAutor|OFF}}"""
            re_page = RePage(self.page_mock)
            self.task.re_page = re_page
            article = re_page.splitted_article_list[0]
            compare(({}, ["wp_link"]), self.task._fetch_wp_link(article))
            compare(({}, ["ws_link"]), self.task._fetch_ws_link(article))

    def test_sortkey(self):
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
|SORTIERUNG=Abalas limen
}}
text.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({"sort_key": "Abalas limen"}, []), SCANTask._fetch_sort_key(article))

        self.text_mock.return_value = """{{REDaten
|BAND=I,1
}}
text.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({}, ["sort_key"]), SCANTask._fetch_sort_key(article))

    def test_lemma(self):
        self.title_mock.return_value = "RE:Aal"
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
}}
text.
{{REAutor|OFF}}"""
        re_page = RePage(self.page_mock)
        article = re_page.splitted_article_list[0]
        task = SCANTask(None, self.logger)
        task.re_page = re_page
        compare(({"lemma": "Aal"}, []), task._fetch_lemma(article))

    @file_data("test_data/register_scanner/test_proof_read.yml")
    def test_proof_read(self, text, result):
        self.title_mock.return_value = "RE:Aal"
        self.text_mock.return_value = text
        re_page = RePage(self.page_mock)
        article = re_page.splitted_article_list[0]
        task = SCANTask(None, self.logger)
        task.re_page = re_page
        compare(result, task._fetch_proof_read(article))

    @file_data("test_data/register_scanner/test_redirect.yml")
    def test_redirect(self, text, result):
        task = SCANTask(None, self.logger)
        self.text_mock.return_value = text
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(result, task._fetch_redirect(article))

    @file_data("test_data/register_scanner/test_previous.yml")
    def test_previous(self, text, result):
        self.text_mock.return_value = text
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(result, SCANTask._fetch_previous(article))

    @file_data("test_data/register_scanner/test_next.yml")
    def test_next(self, text, result):
        self.text_mock.return_value = text
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(result, SCANTask._fetch_next(article))

    @file_data("test_data/register_scanner/test_pages_simple.yml")
    def test_pages(self, text, expect):
        task = SCANTask(None, self.logger)
        self.title_mock.return_value = "RE:Aal"
        self.text_mock.return_value = text
        re_page = RePage(self.page_mock)
        task.re_page = re_page
        article = re_page.splitted_article_list[0]
        compare(expect, task._fetch_pages(article))

    @file_data("test_data/register_scanner/test_pages_complex.yml")
    def test_pages_complex(self, text, expect):
        with LogCapture():
            task = SCANTask(None, self.logger)
            self.title_mock.return_value = "RE:Aal"
            self.text_mock.return_value = text
            re_page = RePage(self.page_mock)
            task.re_page = re_page
            article = re_page.splitted_article_list[0]
            compare(expect, task._fetch_pages(article))

    def test_fetch_from_properties(self):
        with LogCapture():
            self.title_mock.return_value = "RE:Aal"
            self.text_mock.return_value = """{{REDaten
|BAND=I,1
|VORGÄNGER=Lemma Previous
|NACHFOLGER=Lemma Next
|WP=Aal_wp_link
|WS=Aal_ws_link
|SORTIERUNG=Aal
|VERWEIS=ON
|KORREKTURSTAND=korrigiert
}}
text.
{{REAutor|OFF}}"""
            task = SCANTask(None, self.logger)
            task.re_page = RePage(self.page_mock)
            task._process_from_article_list()
            post_lemma = task.registers["I,1"].get_lemma_by_name("Aal")
            compare("w:de:Aal_wp_link", post_lemma.lemma_dict["wp_link"])
            compare("s:de:Aal_ws_link", post_lemma.lemma_dict["ws_link"])
            compare("Aal", post_lemma.lemma_dict["sort_key"])
            compare(2, post_lemma.lemma_dict["proof_read"])
            compare(True, post_lemma.lemma_dict["redirect"])
            compare("Lemma Previous", post_lemma.lemma_dict["previous"])
            compare("Lemma Next", post_lemma.lemma_dict["next"])

    def test_fetch_from_properties_self_append(self):
        with LogCapture():
            copy_tst_data("I_1_self_append", "I_1")
            self.title_mock.return_value = "RE:Aal"
            self.text_mock.return_value = """{{REDaten
|BAND=I,1
|VORGÄNGER=Lemma Previous
|NACHFOLGER=Lemma Next
|WP=Aal_wp_link
|WS=Aal_ws_link
|SORTIERUNG=Aal
|VERWEIS=ON
}}
text.
{{REAutor|OFF}}
{{REDaten
|BAND=I,1
|VORGÄNGER=Lemma Previous2
|NACHFOLGER=Lemma Next2
}}
text.
{{REAutor|OFF}}"""
            task = SCANTask(None, self.logger)
            task.re_page = RePage(self.page_mock)
            task._process_from_article_list()
            post_lemma = task.registers["I,1"].get_lemma_by_name("Aal")
            compare("w:de:Aal_wp_link", post_lemma.lemma_dict["wp_link"])
            compare("s:de:Aal_ws_link", post_lemma.lemma_dict["ws_link"])
            compare("Aal", post_lemma.lemma_dict["sort_key"])
            compare(True, post_lemma.lemma_dict["redirect"])
            compare("Lemma Previous", post_lemma.lemma_dict["previous"])
            compare("Lemma Next", post_lemma.lemma_dict["next"])
            post_lemma_append = task.registers["I,1"].get_lemma_by_name("Aal", self_supplement=True)
            compare("Lemma Previous2", post_lemma_append.lemma_dict["previous"])
            compare("Lemma Next2", post_lemma_append.lemma_dict["next"])

    def test_fetch_from_properties_lemma_not_found(self):
        self.title_mock.return_value = "RE:Aas"
        self.text_mock.return_value = """{{REDaten
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

    @skip("I must mock this. For now I use this test in development.")
    def test_get_wd_sitelink(self):
        WS_WIKI = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")
        self.task.re_page = RePage(pywikibot.Page(WS_WIKI, "RE:Demetrios 79"))
        compare(({'wp_link': 'w:en:Demetrius the Chronographer'}, []),
                self.task._fetch_wp_link(self.task.re_page.splitted_article_list[0]))
        compare(({'ws_link': 's:de:Apokryphen/Demetrius der Chronograph'}, []),
                self.task._fetch_ws_link(self.task.re_page.splitted_article_list[0]))
        compare(({'wd_link': 'd:Q3705296'}, []),
                self.task._fetch_wd_link(self.task.re_page.splitted_article_list[0]))
