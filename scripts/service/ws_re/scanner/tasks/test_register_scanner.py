from pathlib import Path
from unittest import mock

from git import Repo
from testfixtures import compare, LogCapture, StringComparison

from scripts.service.ws_re.register.author import Authors
from scripts.service.ws_re.register.base import _REGISTER_PATH
from scripts.service.ws_re.register.test_base import clear_tst_path, _TEST_REGISTER_PATH, \
    copy_tst_data
from scripts.service.ws_re.register.volume import VolumeRegister
from scripts.service.ws_re.scanner.tasks.register_scanner import SCANTask
from scripts.service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from scripts.service.ws_re.template.re_page import RePage


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


class TestSCANTask(TaskTestWithRegister):
    def setUp(self):
        super().setUp()
        copy_tst_data("I_1_base", "I_1")
        copy_tst_data("authors", "authors")
        copy_tst_data("authors_mapping", "authors_mapping")
        self.task = SCANTask(None, self.logger)

    def test_pushing_nothing_to_push(self):
        with mock.patch("scripts.service.ws_re.scanner.tasks.register_scanner.Repo", mock.Mock(spec=Repo)) as repo_mock:
            repo_mock().index.diff.return_value = []
            self.task._push_changes()
            compare(3, len(repo_mock.mock_calls))
            compare(mock.call(search_parent_directories=True), repo_mock.mock_calls[1])
            compare("().index.diff", repo_mock.mock_calls[2][0])

    def test_pushing_changes(self):
        with LogCapture():
            with mock.patch("scripts.service.ws_re.scanner.tasks.register_scanner.Repo", mock.Mock(spec=Repo)) as repo_mock:
                repo_mock().index.diff.return_value = ["Something has changed"]
                self.task._push_changes()
                compare(8, len(repo_mock.mock_calls))
                compare(mock.call(search_parent_directories=True), repo_mock.mock_calls[1])
                compare("().index.diff", repo_mock.mock_calls[2][0])
                compare("().git.checkout", repo_mock.mock_calls[3][0])
                compare("-b", repo_mock.mock_calls[3][1][0])
                compare(StringComparison(r"\d{6}_\d{6}_updating_registers"), repo_mock.mock_calls[3][1][1])
                compare("().git.add", repo_mock.mock_calls[4][0])
                compare(StringComparison(r".*/scripts/service/ws_re/register/data"), repo_mock.mock_calls[4][1][0])
                compare("().index.commit", repo_mock.mock_calls[5][0])
                compare(StringComparison(r"Updating the register at \d{6}_\d{6}"), repo_mock.mock_calls[5][1][0])
                compare("().git.push", repo_mock.mock_calls[6][0])
                compare("().git.checkout", repo_mock.mock_calls[7][0])

    def test_fetch_wikipedia_wikisource_link(self):
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
|WP=Lemma
|WS=WsLemma
}}
text.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({"wp_link": "w:de:Lemma"}, []), SCANTask._fetch_wp_link(article))
        compare(({"ws_link": "s:de:WsLemma"}, []), SCANTask._fetch_ws_link(article))

    def test_fetch_wikipedia_link_no_link(self):
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
}}
text.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({}, ["wp_link"]), SCANTask._fetch_wp_link(article))
        compare(({}, ["ws_link"]), SCANTask._fetch_ws_link(article))

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
        task.re_page =  re_page
        compare(({"lemma": "Aal"}, []), task._fetch_lemma(article))

    def test_redirect(self):
        task = SCANTask(None, self.logger)
        # redirect from the properties
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
|VERWEIS=ON
}}
text.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({"redirect": True}, []), task._fetch_redirect(article))
        # only a property ... no real link
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
|VERWEIS=OFF
}}
text.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({}, ["redirect"]), task._fetch_redirect(article))
        # fetch a real link from the text {{RE siehe|...
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
|VERWEIS=ON
}}
'''Ad Algam''' s. {{SperrSchrift|{{RE siehe|Turris ad Algam}}}}.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({"redirect": "Turris ad Algam"}, []), task._fetch_redirect(article))
        # fetch a real link from the text [[RE:...
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
|VERWEIS=ON
}}
'''2)''' s. [[RE:Amantia 2|{{SperrSchrift|Amantia}} Nr.&nbsp;2]].
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({"redirect": "Amantia 2"}, []), task._fetch_redirect(article))

    def test_previous(self):
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
|VG=Lemma Previous
}}
text.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({"previous": "Lemma Previous"}, []), SCANTask._fetch_previous(article))
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
|VG=OFF
}}
text.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({}, ["previous"]), SCANTask._fetch_previous(article))
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
}}
text.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({}, ["previous"]), SCANTask._fetch_previous(article))

    def test_next(self):
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
|NF=Lemma Next
}}
text.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({"next": "Lemma Next"}, []), SCANTask._fetch_next(article))
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
|NF=OFF
}}
text.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({}, ["next"]), SCANTask._fetch_next(article))
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
}}
text.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({}, ["next"]), SCANTask._fetch_next(article))

    def test_pages_simple(self):
        task = SCANTask(None, self.logger)
        self.title_mock.return_value = "RE:Aal"

        self.text_mock.return_value = """{{REDaten
|BAND=S I
|SPALTE_START=264
|SPALTE_END=265
}}
text.
{{REAutor|Autor.}}"""
        re_page = RePage(self.page_mock)
        task.re_page = re_page
        article = re_page.splitted_article_list[0]
        expected_dict = {"chapters": [{"start": 264,  "end": 265, "author": "Autor."}]}
        compare((expected_dict, []), task._fetch_pages(article))

        self.text_mock.return_value = """{{REDaten
|BAND=S I
|SPALTE_START=264
|SPALTE_END=OFF
}}
text.
{{REAutor|Autor.}}"""
        re_page = RePage(self.page_mock)
        task.re_page = re_page
        article = re_page.splitted_article_list[0]
        expected_dict = {"chapters": [{"start": 264, "end": 264, "author": "Autor."}]}
        compare((expected_dict, []), task._fetch_pages(article))

        self.text_mock.return_value = """{{REDaten
|BAND=S I
|SPALTE_START=264
|SPALTE_END=
}}
text.
{{REAutor|Autor.}}"""
        re_page = RePage(self.page_mock)
        task.re_page = re_page
        article = re_page.splitted_article_list[0]
        expected_dict = {"chapters": [{"start": 264, "end": 264, "author": "Autor."}]}
        compare((expected_dict, []), task._fetch_pages(article))

        self.text_mock.return_value = """{{REDaten
|BAND=S I
|SPALTE_START=264
|SPALTE_END=264
}}
text.
{{REAutor|OFF}}"""
        re_page = RePage(self.page_mock)
        task.re_page = re_page
        article = re_page.splitted_article_list[0]
        expected_dict = {"chapters": [{"start": 264, "end": 264}]}
        compare((expected_dict, []), task._fetch_pages(article))

    def test_pages_complex_bithynia(self):
        with LogCapture():
            task = SCANTask(None, self.logger)
            self.title_mock.return_value = "RE:Aal"

            with open(Path(__file__).parent.joinpath("test_data/RE_Bithynia.txt"), encoding="utf-8") as test_file:
                self.text_mock.return_value = test_file.read()
            re_page = RePage(self.page_mock)
            task.re_page = re_page
            article = re_page.splitted_article_list[0]
            expected_dict = {"chapters": [{"start": 507, "end": 510, "author": "Ruge."},
                                          {"start": 511, "end": 524, "author": "Ed. Meyer."},
                                          {"start": 524, "end": 539, "author": "Brandis."}]}
            compare((expected_dict, []), task._fetch_pages(article))

    def test_pages_complex_elis(self):
        with LogCapture():
            task = SCANTask(None, self.logger)
            self.title_mock.return_value = "RE:Aal"
            with open(Path(__file__).parent.joinpath("test_data/RE_Elis 1.txt"), encoding="utf-8") as test_file:
                self.text_mock.return_value = test_file.read()
            re_page = RePage(self.page_mock)
            task.re_page = re_page
            article = re_page.splitted_article_list[0]
            expected_dict = {"chapters": [{"start": 2369, "end": 2369, "author": "Philippson."},
                                          {"start": 2369, "end": 2432, "author": "Swoboda."}]}
            compare((expected_dict, []), task._fetch_pages(article))

    def test_pages_complex_abuccius(self):
        with LogCapture():
            task = SCANTask(None, self.logger)
            self.title_mock.return_value = "RE:Aal"
            with open(Path(__file__).parent.joinpath("test_data/RE_L. Abuccius.txt"), encoding="utf-8") as test_file:
                self.text_mock.return_value = test_file.read()
            re_page = RePage(self.page_mock)
            task.re_page = re_page
            article = re_page.splitted_article_list[0]
            expected_dict = {"chapters": [{"start": 124, "end": 124, "author": "Klebs."},
                                          {"start": 125, "end": 125, "author": "v. Rohden."}]}
            compare((expected_dict, []), task._fetch_pages(article))

    def test_pages_complex_plinius(self):
        with LogCapture():
            task = SCANTask(None, self.logger)
            self.title_mock.return_value = "RE:Aal"
            # if the re_page is too complex (import of other pages during page construction) return empty result sets
            with open(Path(__file__).parent.joinpath("test_data/RE_Plinius 5.txt"), encoding="utf-8") as test_file:
                self.text_mock.return_value = test_file.read()
            re_page = RePage(self.page_mock)
            task.re_page = re_page
            article = re_page.splitted_article_list[0]
            expected_dict = {}
            compare((expected_dict, []), task._fetch_pages(article))

    def test_pages_complex_mitarbeiter(self):
        with LogCapture():
            task = SCANTask(None, self.logger)
            self.title_mock.return_value = "RE:Aal"
            # if the pages are non numeric return nothing
            with open(Path(__file__).parent.joinpath("test_data/RE_Mitarbeiter-Verzeichnis.txt"), encoding="utf-8") as test_file:
                self.text_mock.return_value = test_file.read()
            re_page = RePage(self.page_mock)
            task.re_page = re_page
            article = re_page.splitted_article_list[0]
            expected_dict = {}
            compare((expected_dict, []), task._fetch_pages(article))

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
            log_catcher.check(mock.ANY, ("Test", "ERROR", StringComparison("No available Lemma in Registers for issue I,1 .* Reason is:.*")))
