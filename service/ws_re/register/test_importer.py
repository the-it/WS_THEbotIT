# pylint: disable=protected-access,no-self-use
from types import SimpleNamespace
from unittest import TestCase, mock

from service.ws_re.register.authors import Authors
from service.ws_re.register.importer import ReImporter
from service.ws_re.register.lemma import Lemma
from service.ws_re.register.registers import Registers
from service.ws_re.register.test_base import BaseTestRegister
from service.ws_re.template import ReDatenException
from service.ws_re.template.article import Article
from service.ws_re.template.re_page import RePage
from service.ws_re.volumes import Volumes
from tools.bots.test_base import TestCloudBase
from tools.test import real_wiki_test


class TestReImporter(TestCase):
    @real_wiki_test
    def test_adjust_end_column(self):
        registers = Registers()
        register = registers["XVI,1"]
        for idx, article in enumerate(register):
            if article.lemma == "Molorchos":
                # start test
                pre_1 = """{{REDaten
|BAND=XVI,1
|SPALTE_START=13
|SPALTE_END=OFF
|VORGÄNGER=Molorchia
|NACHFOLGER=Μόλος 1
}}
'''Molorchos'''
[...]
{{REAutor|J. Pley.}}"""
                self.assertTrue("SPALTE_END=14" in ReImporter.adjust_end_column(pre_1, register, idx))
                pre_2 = """{{REDaten
|BAND=XVI,1
|SPALTE_START=12
|SPALTE_END=OFF
|VORGÄNGER=Molorchia
|NACHFOLGER=Μόλος 1
}}
'''Molorchos'''
[...]
{{REAutor|J. Pley.}}"""
                # not clear don't do shit
                self.assertTrue("SPALTE_END=OFF" in ReImporter.adjust_end_column(pre_2, register, idx))
                # index out of range
                self.assertTrue("SPALTE_END=OFF" in ReImporter.adjust_end_column(pre_2, register, 9999))
                pre_3 = """{{REDaten
|BAND=XVI,1
|SPALTE_START=nothing
|SPALTE_END=OFF
|VORGÄNGER=Molorchia
|NACHFOLGER=Μόλος 1
}}
'''Molorchos'''
[...]
{{REAutor|J. Pley.}}"""
                # can't determine start column
                self.assertTrue("SPALTE_END=OFF" in ReImporter.adjust_end_column(pre_3, register, idx))
                pre_4 = """{{REDaten
|BAND=XVI,1
|SPALTE_START=14
|SPALTE_END=OFF
|VORGÄNGER=Molorchia
|NACHFOLGER=Μόλος 1
}}
'''Molorchos'''
[...]
{{REAutor|J. Pley.}}"""
                # start on the same column like follow article
                self.assertTrue("SPALTE_END=OFF" in ReImporter.adjust_end_column(pre_4, register, idx))


class TestGetTextBackup(BaseTestRegister):
    def setUp(self):
        self.authors = Authors()
        self.volume = Volumes()["I,1"]

    def _make_lemma(
        self,
        lemma: str,
        previous: str | None = None,
        next_: str | None = None,
        chapters: list[dict] | None = None,
        short_description: str | None = None,
    ) -> Lemma:
        lemma_dict = {"lemma": lemma}
        if previous is not None:
            lemma_dict["previous"] = previous
        if next_ is not None:
            lemma_dict["next"] = next_
        if chapters is not None:
            lemma_dict["chapters"] = chapters
        if short_description is not None:
            lemma_dict["short_description"] = short_description
        return Lemma.from_dict(lemma_dict, self.volume, self.authors)

    def test_uses_article_neighbors_when_set(self):
        article = self._make_lemma("Main", previous="Pre", next_="Post")
        pre = self._make_lemma("OtherPre")
        post = self._make_lemma("OtherPost")
        result = ReImporter.get_text_backup("I,1", article, pre, post)
        self.assertIn("|VORGÄNGER=Pre", result)
        self.assertIn("|NACHFOLGER=Post", result)

    def test_falls_back_to_neighbor_lemma_titles(self):
        article = self._make_lemma("Main")
        pre = self._make_lemma("NeighborPre")
        post = self._make_lemma("NeighborPost")
        result = ReImporter.get_text_backup("I,1", article, pre, post)
        self.assertIn("|VORGÄNGER=NeighborPre", result)
        self.assertIn("|NACHFOLGER=NeighborPost", result)

    def test_empty_when_no_source_and_no_neighbors(self):
        article = self._make_lemma("Main")
        result = ReImporter.get_text_backup("I,1", article)
        self.assertIn("|VORGÄNGER=\n", result)
        self.assertIn("|NACHFOLGER=\n", result)

    def test_mixed_article_and_neighbor(self):
        article = self._make_lemma("Main", previous="Pre")
        post = self._make_lemma("NeighborPost")
        result = ReImporter.get_text_backup("I,1", article, None, post)
        self.assertIn("|VORGÄNGER=Pre", result)
        self.assertIn("|NACHFOLGER=NeighborPost", result)

    def test_columns_author_and_short_description_from_the_chapter(self):
        article = self._make_lemma(
            "Main", chapters=[{"start": 12, "end": 14, "author": "Some Author."}], short_description="a short text"
        )
        result = ReImporter.get_text_backup("I,1", article)
        self.assertIn("|SPALTE_START=12", result)
        self.assertIn("|SPALTE_END=14", result)
        self.assertIn("|KURZTEXT=a short text", result)
        self.assertIn("{{REAutor|Some Author.}}", result)

    def test_no_chapter_at_all(self):
        article = self._make_lemma("Main")
        result = ReImporter.get_text_backup("I,1", article)
        self.assertIn("|SPALTE_START=OFF", result)
        self.assertIn("|SPALTE_END=OFF", result)
        self.assertIn("|KURZTEXT=\n", result)
        self.assertIn("{{REAutor|OFF}}", result)

    def test_chapter_without_end_and_author(self):
        article = self._make_lemma("Main", chapters=[{"start": 12}])
        result = ReImporter.get_text_backup("I,1", article)
        self.assertIn("|SPALTE_START=12", result)
        self.assertIn("|SPALTE_END=OFF", result)
        self.assertIn("{{REAutor|OFF}}", result)

    def test_start_column_falls_back_to_predecessor_end_column(self):
        article = self._make_lemma("Main")
        pre = self._make_lemma("Pre", chapters=[{"start": 12, "end": 14}])
        result = ReImporter.get_text_backup("I,1", article, pre)
        self.assertIn("|SPALTE_START=14", result)

    def test_start_column_falls_back_to_predecessor_start_column_without_end(self):
        article = self._make_lemma("Main")
        pre = self._make_lemma("Pre", chapters=[{"start": 12}])
        result = ReImporter.get_text_backup("I,1", article, pre)
        self.assertIn("|SPALTE_START=12", result)


def _article(band: str, short_text: str = "") -> str:
    return (
        f"{{{{REDaten\n|BAND={band}\n|KURZTEXT={short_text}\n|NACHTRAG=OFF\n|ÜBERSCHRIFT=OFF\n}}}}"
        f"\ntext {band}\n{{{{REAutor|Some Author.}}}}"
    )


class TestAddArticleToLemma(TestCase):
    @mock.patch("service.ws_re.template.re_page.pywikibot.Page")
    @mock.patch("service.ws_re.template.re_page.pywikibot.Page.text", new_callable=mock.PropertyMock)
    # pylint: disable=arguments-differ
    def setUp(self, text_mock, page_mock):
        self.page_mock = page_mock
        self.text_mock = text_mock
        type(self.page_mock).text = self.text_mock

    def _re_page(self, *parts: str) -> RePage:
        self.text_mock.return_value = "\n".join(parts)
        return RePage(self.page_mock)

    def test_position_before_later_issue(self):
        re_page = self._re_page(_article("I A,1"), _article("R"))
        self.assertEqual(1, ReImporter.get_insert_position(re_page, "S XIV"))

    def test_position_in_front_of_all_articles(self):
        re_page = self._re_page(_article("R"))
        self.assertEqual(0, ReImporter.get_insert_position(re_page, "I A,1"))

    def test_position_behind_all_articles(self):
        re_page = self._re_page(_article("I A,1"))
        self.assertEqual(1, ReImporter.get_insert_position(re_page, "S XIV"))

    def test_position_in_front_of_categories(self):
        re_page = self._re_page(_article("I A,1"), "[[Kategorie:RE:Stammdaten überprüfen]]")
        self.assertEqual(1, ReImporter.get_insert_position(re_page, "S XIV"))

    def test_position_behind_text_of_last_article(self):
        re_page = self._re_page(_article("I A,1"), "<references/>")
        self.assertEqual(2, ReImporter.get_insert_position(re_page, "S XIV"))

    def test_get_short_text(self):
        re_page = self._re_page(_article("I A,1", "a short text"), _article("R", "another short text"))
        self.assertEqual("a short text", ReImporter.get_short_text(re_page))

    def test_get_short_text_of_a_later_article(self):
        re_page = self._re_page(_article("I A,1"), _article("R", "another short text"))
        self.assertEqual("another short text", ReImporter.get_short_text(re_page))

    def test_get_short_text_no_short_text_present(self):
        re_page = self._re_page(_article("I A,1"), _article("R"))
        self.assertEqual("", ReImporter.get_short_text(re_page))

    def test_split_trailing_categories(self):
        re_page = self._re_page(
            _article("I A,1"), "<references/>\n\n[[Kategorie:RE:Stammdaten überprüfen]]\n[[Kategorie:Tada]]"
        )
        ReImporter.split_trailing_categories(re_page)
        self.assertEqual("<references/>", re_page[1])
        self.assertEqual("[[Kategorie:RE:Stammdaten überprüfen]]\n[[Kategorie:Tada]]", re_page[2])
        self.assertEqual(2, ReImporter.get_insert_position(re_page, "S XIV"))

    def test_split_trailing_categories_nothing_to_split(self):
        re_page = self._re_page(_article("I A,1"), "[[Kategorie:Tada]]")
        ReImporter.split_trailing_categories(re_page)
        self.assertEqual(2, len(re_page))
        re_page = self._re_page(_article("I A,1"), "<references/>")
        ReImporter.split_trailing_categories(re_page)
        self.assertEqual(2, len(re_page))
        re_page = self._re_page(_article("I A,1"))
        ReImporter.split_trailing_categories(re_page)
        self.assertEqual(1, len(re_page))

    def test_no_position_issue_already_there(self):
        re_page = self._re_page(_article("I A,1"), _article("S XIV"), _article("R"))
        self.assertIsNone(ReImporter.get_insert_position(re_page, "S XIV"))

    def test_unknown_issue_on_page(self):
        re_page = self._re_page(_article("Tada"))
        with self.assertRaises(ReDatenException):
            ReImporter.get_insert_position(re_page, "S XIV")

    def test_adjust_nachtrag(self):
        re_page = self._re_page(_article("I A,1"), _article("S XIV"), _article("R"))
        ReImporter.adjust_nachtrag(re_page)
        flags = [(article["NACHTRAG"].value, article["ÜBERSCHRIFT"].value) for article in re_page.only_articles]
        self.assertEqual([(False, False), (True, True), (True, False)], flags)

    def test_insert_article_in_page(self):
        re_page = self._re_page(_article("I A,1"), "[[Kategorie:RE:Stammdaten überprüfen]]")
        position = ReImporter.get_insert_position(re_page, "S XIV")
        re_page.insert(position, Article.from_text(_article("S XIV")))
        ReImporter.adjust_nachtrag(re_page)
        page_text = str(re_page)
        self.assertLess(page_text.index("BAND=I A,1"), page_text.index("BAND=S XIV"))
        self.assertLess(page_text.index("BAND=S XIV"), page_text.index("[[Kategorie:"))


NEULAND = """{{REDaten
|BAND=S XIV
|SPALTE_START=100
|KORREKTURSTAND=Platzhalter
}}
'''Tada'''
{{REAutor|Some Author.}}
1 „RE:Tada“
"""


class PageDouble:
    """minimal replacement for a pywikibot page, it only knows the things the importer uses"""

    def __init__(self, title: str = "RE:Tada", text: str = "", exists: bool = True, redirect: bool = False):
        self.text = text
        self.save_reason = ""
        self._title = title
        self._exists = exists
        self._redirect = redirect
        self._protection: dict[str, tuple[str, str]] = {}

    def title(self) -> str:
        return self._title

    def exists(self) -> bool:
        return self._exists

    def isRedirectPage(self) -> bool:  # naming is given by pywikibot
        return self._redirect

    def protection(self) -> dict[str, tuple[str, str]]:
        return self._protection

    def protect_for_sysop(self):
        self._protection = {"edit": ("sysop", "infinity")}

    def save(self, reason: str, bot: bool = True):  # pylint: disable=unused-argument
        self.save_reason = reason


class LemmaDouble:
    """minimal replacement for a register lemma"""

    def __init__(self, lemma: str, proof_read: int | None = None, band: str = "S XIV", start: int | None = 100):
        self.lemma = lemma
        self.proof_read = proof_read
        self.volume = SimpleNamespace(name=band)
        self.previous = "Pre"
        self.next = "Post"
        self.short_description = "a short text"
        self.chapter_objects = [SimpleNamespace(start=start, end=None, author="Some Author.")] if start else []


class RegisterDouble:
    """minimal replacement for a volume register"""

    def __init__(self, lemmas: list[LemmaDouble], band: str = "S XIV"):
        self._lemmas = lemmas
        self.volume = SimpleNamespace(name=band)

    def __iter__(self):
        yield from self._lemmas

    def __getitem__(self, idx: int) -> LemmaDouble:
        return self._lemmas[idx]


class ImporterTestCase(TestCloudBase):
    def setUp(self):
        self.page_mock = self._start_patch("Page")
        self.page_mock.return_value.text = NEULAND
        self.category_mock = self._start_patch("Category")
        self.category_mock.return_value.articles.return_value = []
        self.registers_mock = self._start_patch("Registers")
        self._start_patch("get_author_mapping").return_value = {}
        self.importer = ReImporter(wiki=None, debug=True, log_to_screen=False, log_to_wiki=False)

    def _start_patch(self, name: str) -> mock.MagicMock:
        patcher = mock.patch(f"service.ws_re.register.importer.{name}")
        self.addCleanup(patcher.stop)
        return patcher.start()


class TestReImporterInit(ImporterTestCase):
    def test_articles_from_neuland(self):
        self.assertEqual({"S XIV": {"Tada": NEULAND.split("\n1 „RE:")[0]}}, self.importer.new_articles)

    def test_get_text(self):
        self.assertIn("BAND=S XIV", str(self.importer.get_text("S XIV", "Tada")))
        self.assertIsNone(self.importer.get_text("S XIV", "Other Lemma"))
        self.assertIsNone(self.importer.get_text("I,1", "Tada"))

    def test_max_create_limited_by_the_category(self):
        self.assertEqual(self.importer._PER_NIGHT, self.importer.max_create)
        self.category_mock.return_value.articles.return_value = ["lemma"] * (ReImporter._MAX_CAT - 5)
        importer = ReImporter(wiki=None, debug=True, log_to_screen=False, log_to_wiki=False)
        self.assertEqual(5, importer.max_create)


class TestCreateLemma(ImporterTestCase):
    def test_create_lemma(self):
        page = PageDouble(exists=False)
        with mock.patch("service.ws_re.register.importer.save_if_changed") as save_mock:
            self.importer._create_lemma(page, _article("S XIV"))
        text, reason = save_mock.call_args.args[1], save_mock.call_args.args[2]
        self.assertIn("[[Kategorie:RE:Stammdaten überprüfen]]", text)
        self.assertIn("[[Kategorie:RE:Kurztext überprüfen]]", text)
        self.assertEqual("Automatisch generiert", reason)


class TestAddArticle(ImporterTestCase):
    def test_add_article(self):
        page = PageDouble(text=_article("I A,1", "a checked short text"))
        self.assertTrue(self.importer._add_article(page, "S XIV", _article("S XIV", "short text of the register")))
        self.assertLess(page.text.index("BAND=I A,1"), page.text.index("BAND=S XIV"))
        # the short text of the lemma wins, so the category isn't needed
        self.assertEqual(2, page.text.count("KURZTEXT=a checked short text"))
        self.assertNotIn("[[Kategorie:RE:Kurztext überprüfen]]", page.text)
        self.assertIn("[[Kategorie:RE:Stammdaten überprüfen]]", page.text)
        self.assertEqual("Automatisch ergänzter Artikel aus Band S XIV", page.save_reason)

    def test_add_article_no_short_text_on_the_page(self):
        page = PageDouble(text=_article("I A,1"))
        self.assertTrue(self.importer._add_article(page, "S XIV", _article("S XIV", "short text of the register")))
        self.assertIn("KURZTEXT=short text of the register", page.text)
        self.assertIn("[[Kategorie:RE:Kurztext überprüfen]]", page.text)

    def test_add_article_no_start_column(self):
        page = PageDouble(text=_article("I A,1"))
        self.assertFalse(self.importer._add_article(page, "S XIV", "{{REDaten\n|SPALTE_START=OFF\n}}"))
        self.assertEqual("", page.save_reason)

    def test_add_article_lemma_is_a_redirect(self):
        page = PageDouble(text="#REDIRECT [[RE:Tada 1]]", redirect=True)
        self.assertFalse(self.importer._add_article(page, "S XIV", _article("S XIV")))

    def test_add_article_page_cant_be_parsed(self):
        page = PageDouble(text="no article at all")
        self.assertFalse(self.importer._add_article(page, "S XIV", _article("S XIV")))

    def test_add_article_unknown_issue_on_the_page(self):
        page = PageDouble(text=_article("Tada"))
        self.assertFalse(self.importer._add_article(page, "S XIV", _article("S XIV")))

    def test_add_article_issue_already_present(self):
        page = PageDouble(text=_article("S XIV"))
        self.assertFalse(self.importer._add_article(page, "S XIV", _article("S XIV")))
        self.assertEqual("", page.save_reason)

    def test_add_article_new_article_cant_be_parsed(self):
        page = PageDouble(text=_article("I A,1"))
        self.assertFalse(self.importer._add_article(page, "S XIV", "{{REDaten\n|SPALTE_START=1\n}}\nno author"))

    def test_add_article_page_is_protected(self):
        page = PageDouble(text=_article("I A,1"))
        page.protect_for_sysop()
        self.assertFalse(self.importer._add_article(page, "S XIV", _article("S XIV")))
        self.assertEqual("", page.save_reason)


class TestTask(ImporterTestCase):
    def _run_task(self, lemmas: list[LemmaDouble], pages: dict[str, PageDouble]) -> bool:
        self.importer.registers = SimpleNamespace(volumes={"S XIV": RegisterDouble(lemmas)})
        self.page_mock.side_effect = lambda wiki, title: pages[title]
        return self.importer.task()

    def test_task_creates_and_adds(self):
        pages = {
            "RE:New Lemma": PageDouble("RE:New Lemma", exists=False),
            "RE:Old Lemma": PageDouble("RE:Old Lemma", text=_article("I A,1")),
        }
        lemmas = [LemmaDouble("New Lemma"), LemmaDouble("Old Lemma"), LemmaDouble("Done Lemma", proof_read=2)]
        with mock.patch("service.ws_re.register.importer.save_if_changed") as save_mock:
            self.assertTrue(self._run_task(lemmas, pages))
        self.assertEqual(1, save_mock.call_count)
        self.assertIn("BAND=S XIV", save_mock.call_args.args[1])
        self.assertIn("BAND=S XIV", pages["RE:Old Lemma"].text)

    def test_task_stops_at_max_create(self):
        pages = {
            "RE:Lemma 1": PageDouble("RE:Lemma 1", exists=False),
            "RE:Lemma 2": PageDouble("RE:Lemma 2", exists=False),
        }
        lemmas = [LemmaDouble("Lemma 1"), LemmaDouble("Lemma 2")]
        self.importer.max_create = 1
        with mock.patch("service.ws_re.register.importer.save_if_changed") as save_mock:
            self.assertTrue(self._run_task(lemmas, pages))
        self.assertEqual(1, save_mock.call_count)

    def test_task_nothing_to_do_when_the_budget_is_used_up(self):
        lemmas = [LemmaDouble("Lemma 1")]
        self.importer.max_create = 0
        with mock.patch("service.ws_re.register.importer.save_if_changed") as save_mock:
            self.assertTrue(self._run_task(lemmas, {}))
        self.assertEqual(0, save_mock.call_count)

    def test_task_last_lemma_of_the_register_has_no_follower(self):
        pages = {"RE:Lemma 1": PageDouble("RE:Lemma 1", exists=False)}
        with mock.patch("service.ws_re.register.importer.save_if_changed") as save_mock:
            self.assertTrue(self._run_task([LemmaDouble("Lemma 1")], pages))
        self.assertIn("|NACHFOLGER=Post", save_mock.call_args.args[1])
        self.assertIn("|SPALTE_END=OFF", save_mock.call_args.args[1])

    def test_task_end_column_stays_open_if_the_follower_has_no_columns(self):
        pages = {
            "RE:Lemma 1": PageDouble("RE:Lemma 1", exists=False),
            "RE:Lemma 2": PageDouble("RE:Lemma 2", exists=False),
        }
        lemmas = [LemmaDouble("Lemma 1"), LemmaDouble("Lemma 2", start=None)]
        with mock.patch("service.ws_re.register.importer.save_if_changed") as save_mock:
            self.assertTrue(self._run_task(lemmas, pages))
        self.assertIn("|SPALTE_END=OFF", save_mock.call_args_list[0].args[1])

    def test_task_uses_the_article_of_the_neuland_page(self):
        pages = {"RE:Tada": PageDouble("RE:Tada", exists=False)}
        with mock.patch("service.ws_re.register.importer.save_if_changed") as save_mock:
            self.assertTrue(self._run_task([LemmaDouble("Tada")], pages))
        self.assertIn("KORREKTURSTAND=unvollständig", save_mock.call_args.args[1])
