from freezegun import freeze_time
from testfixtures import compare

from service.ws_re.scanner.tasks.correct_pd_dates import COPDTask, Years
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage


@freeze_time("2025-01-01")
class TestCOPDTask(TaskTestCase):
    def setUp(self):
        super().setUp()
        self.task = COPDTask(None, self.logger)

    def test_get_pd_death(self):
        self.page_mock.text = """{{REDaten
|BAND=XII,1
|KEINE_SCHÖPFUNGSHÖHE=ON
|TODESJAHR=
|GEBURTSJAHR=1882
}}
something
{{REAutor|Obst.}}"""
        re_page = RePage(self.page_mock)
        article_list = re_page.splitted_article_list[0]
        compare(Years(None, 1944, 2015), self.task.get_max_pd_year(article_list))

    def test_get_pd_birth(self):
        self.page_mock.text = """{{REDaten
|BAND=XII,1
|KEINE_SCHÖPFUNGSHÖHE=ON
|TODESJAHR=
|GEBURTSJAHR=
}}
something
{{REAutor|Werner Eck.}}"""
        re_page = RePage(self.page_mock)
        article_list = re_page.splitted_article_list[0]
        compare(Years(1939, None, 2090), self.task.get_max_pd_year(article_list))

    def test_set_years_not_relevant_remove_years(self):
        self.page_mock.text = """{{REDaten
|BAND=XIII,2
|KEINE_SCHÖPFUNGSHÖHE=ON
|TODESJAHR=
|GEBURTSJAHR=1882
}}
blub
{{REAutor|Obst.}}"""
        re_page = RePage(self.page_mock)
        article_list = re_page.splitted_article_list[0]
        years = Years(None, 1944, 2015)
        self.task.set_year_values(article_list, years)
        first_article = article_list[0]
        compare(False, first_article["KEINE_SCHÖPFUNGSHÖHE"].value)
        compare("", first_article["GEBURTSJAHR"].value)
        compare("", first_article["TODESJAHR"].value)

    def test_set_years_relevant_flip_years(self):
        self.page_mock.text = """{{REDaten
|BAND=XIII,2
|KEINE_SCHÖPFUNGSHÖHE=OFF
|TODESJAHR=
|GEBURTSJAHR=1882
}}
blub
{{REAutor|Obst.}}"""
        re_page = RePage(self.page_mock)
        article_list = re_page.splitted_article_list[0]
        years = Years(None, 1944, 2015)
        self.task.set_year_values(article_list, years)
        first_article = article_list[0]
        compare(False, first_article["KEINE_SCHÖPFUNGSHÖHE"].value)
        compare("", first_article["GEBURTSJAHR"].value)
        compare("1944", first_article["TODESJAHR"].value)

    def test_set_years_relevant_but_not_protected_anymore_dont_set_years(self):
        self.page_mock.text = """{{REDaten
|BAND=XIII,2
|KEINE_SCHÖPFUNGSHÖHE=OFF
|TODESJAHR=
|GEBURTSJAHR=
}}
blub
{{REAutor|Obst.}}"""
        re_page = RePage(self.page_mock)
        article_list = re_page.splitted_article_list[0]
        years = Years(None, 1944, 2015)
        self.task.set_year_values(article_list, years)
        first_article = article_list[0]
        compare(False, first_article["KEINE_SCHÖPFUNGSHÖHE"].value)
        compare("", first_article["GEBURTSJAHR"].value)
        compare("", first_article["TODESJAHR"].value)
    def test_set_years_relevant_protected_set_years(self):
        self.page_mock.text = """{{REDaten
|BAND=XIII,2
|KEINE_SCHÖPFUNGSHÖHE=OFF
|TODESJAHR=
|GEBURTSJAHR=
}}
blub
{{REAutor|Obst.}}"""
        re_page = RePage(self.page_mock)
        article_list = re_page.splitted_article_list[0]
        years = Years(None, 1955, 2026)
        self.task.set_year_values(article_list, years)
        first_article = article_list[0]
        compare(False, first_article["KEINE_SCHÖPFUNGSHÖHE"].value)
        compare("", first_article["GEBURTSJAHR"].value)
        compare("1955", first_article["TODESJAHR"].value)

    def test_process_newly_public_domain_tj(self):
        """
        article is in public domain since this day and has no height of creation. Defined by death year.
        Expectation: article changed
        """
        self.page_mock.text = """{{REDaten
|BAND=S I
|KEINE_SCHÖPFUNGSHÖHE=ON
|TODESJAHR=1954
}}
bla
{{REAutor|Stein.}}"""
        re_page = RePage(self.page_mock)
        article_list = re_page.splitted_article_list[0]
        years = Years(None, 1954, 2025)
        self.task.set_year_values(article_list, years)
        first_article = article_list[0]
        compare(False, first_article["KEINE_SCHÖPFUNGSHÖHE"].value)
        compare("", first_article["GEBURTSJAHR"].value)
        compare("", first_article["TODESJAHR"].value)

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
        article_list = re_page.splitted_article_list[0]
        years = Years(1870, None, 2025)
        self.task.set_year_values(article_list, years)
        first_article = article_list[0]
        compare(False, first_article["KEINE_SCHÖPFUNGSHÖHE"].value)
        compare("", first_article["GEBURTSJAHR"].value)
        compare("", first_article["TODESJAHR"].value)

    def test_process_newly_public_domain_tj_not_yet(self):
        """
        article is not in public domain since and has no height of creation. Defined by death year.
        Expectation: article not changed
        """
        self.page_mock.text = """{{REDaten
|BAND=S I
|KEINE_SCHÖPFUNGSHÖHE=ON
|TODESJAHR=1955
}}
bla
{{REAutor|Stein.}}"""
        re_page = RePage(self.page_mock)
        article_list = re_page.splitted_article_list[0]
        years = Years(None, 1955, 2026)
        self.task.set_year_values(article_list, years)
        first_article = article_list[0]
        compare(True, first_article["KEINE_SCHÖPFUNGSHÖHE"].value)
        compare("", first_article["GEBURTSJAHR"].value)
        compare("1955", first_article["TODESJAHR"].value)

    def test_process_newly_public_domain_gj_not_yet(self):
        """
        article is not in public domain since and has no height of creation. Defined by birth year.
        Expectation: article not changed
        """
        self.page_mock.text = """{{REDaten
|BAND=S I
|KEINE_SCHÖPFUNGSHÖHE=ON
|GEBURTSJAHR=1900
}}
bla
{{REAutor|Stein.}}"""
        re_page = RePage(self.page_mock)
        article_list = re_page.splitted_article_list[0]
        years = Years(1900, None, 2026)
        self.task.set_year_values(article_list, years)
        first_article = article_list[0]
        compare(True, first_article["KEINE_SCHÖPFUNGSHÖHE"].value)
        compare("1900", first_article["GEBURTSJAHR"].value)
        compare("", first_article["TODESJAHR"].value)

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
        article_list = re_page.splitted_article_list[0]
        years = Years(None, 1950, 2021)
        self.task.set_year_values(article_list, years)
        first_article = article_list[0]
        compare(False, first_article["KEINE_SCHÖPFUNGSHÖHE"].value)
        compare("", first_article["GEBURTSJAHR"].value)
        compare("1950", first_article["TODESJAHR"].value)

    def test_no_author_information(self):
        """
        We have neither a birth nor a death year for the author ... change nothing.
        """
        expectation = """{{REDaten
|BAND=S XIV
|SPALTE_START=104
|SPALTE_END=105
|VORGÄNGER=Claudius 441a
|NACHFOLGER=Clodius 58a
|SORTIERUNG=
|KORREKTURSTAND=Platzhalter
|KURZTEXT=Q. C. Flavianus, c.v., Inhaber mehrerer Priesterämter 4. Jh. n. Chr.
|WIKIPEDIA=
|WIKISOURCE=
|GND=
|KEINE_SCHÖPFUNGSHÖHE=OFF
|TODESJAHR=
|GEBURTSJAHR=1952
|NACHTRAG=OFF
|ÜBERSCHRIFT=OFF
|VERWEIS=OFF
}}
TEXT
{{REAutor|Garth Thomas.}}"""
        self.page_mock.text = expectation
        re_page = RePage(self.page_mock)
        self.task.re_page = re_page
        self.task.task()
        compare(expectation, str(re_page))

    def test_integration(self):
        self.page_mock.text = """{{REDaten
|BAND=XIII,2
|KEINE_SCHÖPFUNGSHÖHE=ON
|TODESJAHR=
|GEBURTSJAHR=1882
}}
blub
{{REAutor|Obst.}}
{{REDaten
|BAND=XII,1
|KEINE_SCHÖPFUNGSHÖHE=ON
|TODESJAHR=
|GEBURTSJAHR=
}}
something
{{REAutor|Werner Eck.}}"""
        re_page = RePage(self.page_mock)
        self.task.re_page = re_page
        self.task.task()
        compare("""{{REDaten
|BAND=XIII,2
|SPALTE_START=
|SPALTE_END=
|VORGÄNGER=
|NACHFOLGER=
|SORTIERUNG=
|KORREKTURSTAND=
|KURZTEXT=
|WIKIPEDIA=
|WIKISOURCE=
|GND=
|KEINE_SCHÖPFUNGSHÖHE=OFF
|TODESJAHR=
|GEBURTSJAHR=
|NACHTRAG=OFF
|ÜBERSCHRIFT=OFF
|VERWEIS=OFF
}}
blub
{{REAutor|Obst.}}
{{REDaten
|BAND=XII,1
|SPALTE_START=
|SPALTE_END=
|VORGÄNGER=
|NACHFOLGER=
|SORTIERUNG=
|KORREKTURSTAND=
|KURZTEXT=
|WIKIPEDIA=
|WIKISOURCE=
|GND=
|KEINE_SCHÖPFUNGSHÖHE=ON
|TODESJAHR=
|GEBURTSJAHR=1939
|NACHTRAG=OFF
|ÜBERSCHRIFT=OFF
|VERWEIS=OFF
}}
something
{{REAutor|Werner Eck.}}""", str(re_page))
