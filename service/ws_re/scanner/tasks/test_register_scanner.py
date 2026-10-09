# pylint: disable=protected-access
from unittest import mock

import pywikibot
from ddt import ddt, file_data
from testfixtures import LogCapture, StringComparison, compare

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
        with mock.patch(
            "service.ws_re.scanner.tasks.register_scanner.SCANTask._get_link_from_wd", mock.Mock(return_value=None)
        ):
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
            task.task()
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

    def test_dont_fetch_generated_lemmas(self):
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
{{REAutor|OFF}}
[[Kategorie:RE:Stammdaten überprüfen]]"""
            task = SCANTask(None, self.logger)
            task.re_page = RePage(self.page_mock)
            pre_lemma_dict = task.registers["I,1"].get_lemma_by_name("Aal").to_dict()
            task.task()
            post_lemma_dict = task.registers["I,1"].get_lemma_by_name("Aal").to_dict()
            compare(pre_lemma_dict, post_lemma_dict)

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

    @staticmethod
    def _article_text(korrekturstand: str, spalte_start: int = 1) -> str:
        return f"""{{{{REDaten
|BAND=I,1
|SPALTE_START={spalte_start}
|KORREKTURSTAND={korrekturstand}
}}}}
text.
{{{{REAutor|OFF}}}}"""

    def _revision(self, timestamp: str, korrekturstand: str | None, spalte_start: int = 1) -> mock.Mock:
        revision = mock.Mock()
        revision.timestamp = pywikibot.Timestamp.fromISOformat(timestamp)
        revision.text = None
        if korrekturstand is not None:
            revision.text = self._article_text(korrekturstand, spalte_start)
        return revision

    def test_get_last_revision_per_day(self):
        revisions = [
            self._revision("2017-10-24T20:00:00Z", "korrigiert"),
            self._revision("2009-03-05T10:00:00Z", "Platzhalter"),
            self._revision("2017-10-24T08:00:00Z", "unkorrigiert"),
            self._revision("2018-01-01T08:00:00Z", None),
        ]
        result = self.task._get_last_revision_per_day(revisions)
        compare(["090305", "171024"], [datestamp for datestamp, _ in result])
        self.assertIn("KORREKTURSTAND=korrigiert", result[1][1])

    def test_add_state_to_history(self):
        history: dict[int, str] = {}
        SCANTask._add_state_to_history(history, 0, "170101")
        SCANTask._add_state_to_history(history, 0, "170102")
        compare({0: "170101"}, history)
        SCANTask._add_state_to_history(history, 2, "170103")
        compare({0: "170101", 2: "170103"}, history)
        SCANTask._add_state_to_history(history, 3, "170104")
        SCANTask._add_state_to_history(history, 1, "170105")
        compare({0: "170101", 1: "170105"}, history)
        SCANTask._add_state_to_history(history, 0, "170106")
        compare({0: "170106"}, history)

    def test_fetch_history(self):
        self.page_mock.text = self._article_text("fertig")
        self.page_mock.revisions.return_value = [
            self._revision("2010-11-20T10:00:00Z", "Platzhalter"),
            self._revision("2012-02-01T10:00:00Z", "unkorrigiert"),
            self._revision("2012-02-01T12:00:00Z", "korrigiert"),
            self._revision("2015-07-14T12:00:00Z", "fertig"),
        ]
        re_page = RePage(self.page_mock)
        self.task.re_page = re_page
        self.task.history = self.task._crawl_history()
        article_list = re_page.splitted_article_list[0]
        compare(({"history": {0: "101120", 2: "120201", 3: "150714"}}, []), self.task._fetch_history(article_list))

    def test_fetch_history_corrupt_revision(self):
        self.page_mock.text = """{{REDaten
|BAND=I,1
|SPALTE_START=1
}}
text.
{{REAutor|OFF}}"""
        corrupt_revision = self._revision("2010-11-20T10:00:00Z", "unkorrigiert")
        corrupt_revision.text = "{{REDaten|BAND=I,1}}\ntext without author"
        self.page_mock.revisions.return_value = [
            corrupt_revision,
            self._revision("2011-11-20T10:00:00Z", "unvollständig"),
        ]
        re_page = RePage(self.page_mock)
        self.task.re_page = re_page
        self.task.history = self.task._crawl_history()
        compare(({"history": {0: "111120"}}, []), self.task._fetch_history(re_page.splitted_article_list[0]))

    def test_fetch_history_corrected_start_column(self):
        self.page_mock.text = self._article_text("unkorrigiert", spalte_start=2)
        self.page_mock.revisions.return_value = [
            self._revision("2010-11-20T10:00:00Z", "Platzhalter", spalte_start=1),
            self._revision("2012-02-01T10:00:00Z", "unkorrigiert", spalte_start=1),
            self._revision("2026-07-17T10:00:00Z", "unkorrigiert", spalte_start=2),
        ]
        re_page = RePage(self.page_mock)
        self.task.re_page = re_page
        self.task.history = self.task._crawl_history()
        compare(
            ({"history": {0: "101120", 1: "120201"}}, []), self.task._fetch_history(re_page.splitted_article_list[0])
        )

    def test_fetch_history_same_issue_twice(self):
        main_article = self._article_text("korrigiert", spalte_start=5)
        self.page_mock.text = f"{main_article}\n{self._article_text('Platzhalter', spalte_start=1)}"
        old_revision = self._revision("2010-11-20T10:00:00Z", None)
        old_revision.text = self._article_text("unkorrigiert", spalte_start=5)
        new_revision = self._revision("2012-02-01T10:00:00Z", None)
        new_revision.text = self.page_mock.text
        self.page_mock.revisions.return_value = [old_revision, new_revision]
        re_page = RePage(self.page_mock)
        self.task.re_page = re_page
        self.task.history = self.task._crawl_history()
        compare(
            ({"history": {1: "101120", 2: "120201"}}, []), self.task._fetch_history(re_page.splitted_article_list[0])
        )
        compare(({"history": {0: "120201"}}, []), self.task._fetch_history(re_page.splitted_article_list[1]))

    def test_fetch_history_not_common_free(self):
        protected_text = self._article_text("korrigiert").replace("|BAND=I,1", "|BAND=I,1\n|TODESJAHR=2000")
        self.page_mock.text = protected_text
        revision = self._revision("2010-11-20T10:00:00Z", None)
        revision.text = protected_text
        self.page_mock.revisions.return_value = [revision]
        re_page = RePage(self.page_mock)
        self.task.re_page = re_page
        self.task.history = self.task._crawl_history()
        compare(({"history": {0: "101120"}}, []), self.task._fetch_history(re_page.splitted_article_list[0]))

    def test_parse_legacy_revision(self):
        layouts = [
            # until 2008 without SPALTE_END
            ("{{RE|I,1|1|Abkürzungen|Aarassos|Aal||unkorrigiert|Flussaale||Pauly-Wissowa I,1, 0001.jpg}}\ntext", "1"),
            # stray empty parameter
            ("{{RE|I,1|4|||Aal|Aba 1|Aarassos||unkorrigiert|||Pauly-Wissowa I,1, 0003.jpg}}\ntext", "4"),
            # with SPALTE_END and embedded templates, no REAutor
            (
                (
                    "{{RE|S I|159|219|Athenadas|Athenaios 9a|Athenai 1a||unkorrigiert|Athen|Athen|"
                    "{{REIA|S I|159}}|{{REIA|S I|219}}}}\ntext"
                ),
                "159",
            ),
        ]
        for text, spalte_start in layouts:
            splitted_article_list = SCANTask._parse_legacy_revision(text)
            compare(1, len(splitted_article_list))
            article = splitted_article_list[0].daten
            compare(spalte_start, article["SPALTE_START"].value)
            compare(1, SCANTask._get_proof_read_state(article))
        compare("S I", SCANTask._parse_legacy_revision(layouts[2][0])[0].daten["BAND"].value)

    def test_fetch_history_legacy_template(self):
        self.page_mock.text = self._article_text("fertig")
        legacy_created = self._revision("2007-06-04T08:00:00Z", None)
        legacy_created.text = "{{RE|I,1|1|Abkürzungen|Aarassos|Aal||unvollständig|Flussaale}}"
        legacy_unkorrigiert = self._revision("2007-06-05T08:00:00Z", None)
        legacy_unkorrigiert.text = (
            "{{RE|I,1|1|4|Abkürzungen|Aarassos|Aal||unkorrigiert|Flussaale}}\ntext\n{{REAutor|Oder.}}"
        )
        self.page_mock.revisions.return_value = [
            legacy_created,
            legacy_unkorrigiert,
            self._revision("2016-11-01T07:26:22Z", "korrigiert"),
            self._revision("2017-01-01T07:26:22Z", "fertig"),
        ]
        re_page = RePage(self.page_mock)
        self.task.re_page = re_page
        self.task.history = self.task._crawl_history()
        compare(
            ({"history": {0: "070604", 1: "070605", 2: "161101", 3: "170101"}}, []),
            self.task._fetch_history(re_page.splitted_article_list[0]),
        )

    def test_fetch_history_no_history(self):
        self.page_mock.text = """{{REDaten
|BAND=I,1
|SPALTE_START=1
}}
text.
{{REAutor|OFF}}"""
        re_page = RePage(self.page_mock)
        self.task.re_page = re_page
        compare(({}, ["history"]), self.task._fetch_history(re_page.splitted_article_list[0]))

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
            log_catcher.check(
                mock.ANY,
                ("Test", "ERROR", StringComparison("No available Lemma in Registers for issue I,1 .* Reason is:.*")),
            )

    @real_wiki_test
    def test_get_wd_sitelink(self):
        WS_WIKI = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")
        self.task.re_page = RePage(pywikibot.Page(WS_WIKI, "RE:Demetrios 79"))
        compare(
            ({"wp_link": "w:en:Demetrius the Chronographer"}, []),
            self.task._fetch_wp_link(self.task.re_page.splitted_article_list[0]),
        )
        compare(
            ({"ws_link": "s:de:Apokryphen/Demetrius der Chronograph"}, []),
            self.task._fetch_ws_link(self.task.re_page.splitted_article_list[0]),
        )
        compare(({"wd_link": "d:Q3705296"}, []), self.task._fetch_wd_link(self.task.re_page.splitted_article_list[0]))
