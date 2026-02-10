from unittest import mock

import pywikibot

from service.ws_re.scanner.tasks.sortkey_from_redirect import SKFRTask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage


class TestSKFRTask(TaskTestCase):
    def setUp(self):
        super().setUp()
        self.task = SKFRTask(None, self.logger)

    def test_sortkey_already_set(self):
        """Test that task returns True if sortkey is already set."""
        self.page_mock.text = """{{REDaten
|BAND=I,1
|SORTIERUNG=Existing Sortkey
}}
text.
{{REAutor|OFF}}"""
        re_page = RePage(self.page_mock)
        self.task.re_page = re_page
        result = self.task.task()
        self.assertTrue(result)
        # Sortkey should not be changed
        self.assertIn("SORTIERUNG=Existing Sortkey", self.page_mock.text)

    def test_no_redirects(self):
        """Test that task returns True if no redirects exist."""
        self.page_mock.text = """{{REDaten
|BAND=I,1
}}
text.
{{REAutor|OFF}}"""
        re_page = RePage(self.page_mock)
        self.task.re_page = re_page

        with mock.patch.object(re_page, 'get_redirects', return_value=[]):
            result = self.task.task()
            self.assertTrue(result)

    def test_redirect_with_better_sortkey(self):
        """Test that redirect with better sortkey is used."""
        self.page_mock.title_str = "RE:Ἀβαριᾶται"
        self.page_mock.text = """{{REDaten
|BAND=I,1
}}
text.
{{REAutor|OFF}}"""

        # Mock redirect page
        redirect_mock = mock.Mock(spec=pywikibot.Page)
        redirect_mock.title.return_value = "RE:Abariatai"

        re_page = RePage(self.page_mock)
        self.task.re_page = re_page

        with mock.patch.object(re_page, 'get_redirects', return_value=[redirect_mock]):
            result = self.task.task()
            self.assertTrue(result)
            # Check that SORTIERUNG was set in the article
            self.assertEqual("Abariatai", re_page.first_article["SORTIERUNG"].value)

    def test_main_lemma_better_than_redirect(self):
        """Test that main lemma is kept if it's better than redirect."""
        self.page_mock.title_str = "RE:Abariatai"
        self.page_mock.text = """{{REDaten
|BAND=I,1
}}
text.
{{REAutor|OFF}}"""

        # Mock redirect with worse sortkey (very different from computed)
        redirect_mock = mock.Mock(spec=pywikibot.Page)
        redirect_mock.title.return_value = "RE:Ἀβαριᾶται Ζωή Χάρις"

        re_page = RePage(self.page_mock)
        self.task.re_page = re_page

        with mock.patch.object(re_page, 'get_redirects', return_value=[redirect_mock]):
            result = self.task.task()
            self.assertTrue(result)
            # Check that SORTIERUNG was NOT set (main lemma is better)
            self.assertEqual("", re_page.first_article["SORTIERUNG"].value)

    def test_multiple_redirects_best_is_chosen(self):
        """Test that the best redirect among multiple is chosen."""
        self.page_mock.title_str = "RE:Αβδηρα"
        self.page_mock.text = """{{REDaten
|BAND=I,1
}}
text.
{{REAutor|OFF}}"""

        # Mock multiple redirects
        redirect1 = mock.Mock(spec=pywikibot.Page)
        redirect1.title.return_value = "RE:Abdera"  # Good match

        redirect2 = mock.Mock(spec=pywikibot.Page)
        redirect2.title.return_value = "RE:Abdhera"  # Even better match

        redirect3 = mock.Mock(spec=pywikibot.Page)
        redirect3.title.return_value = "RE:Something Completely Different"  # Bad match

        re_page = RePage(self.page_mock)
        self.task.re_page = re_page

        with mock.patch.object(re_page, 'get_redirects', return_value=[redirect1, redirect2, redirect3]):
            result = self.task.task()
            self.assertTrue(result)
            # Should use one of the good redirects (Abdera or Abdhera, both better than Greek)
            sortkey = re_page.first_article["SORTIERUNG"].value
            self.assertEqual(sortkey, "Abdera")

    def test_get_redirects_error_handling(self):
        """Test that errors in getting redirects are handled gracefully."""
        self.page_mock.text = """{{REDaten
|BAND=I,1
}}
text.
{{REAutor|OFF}}"""
        re_page = RePage(self.page_mock)
        self.task.re_page = re_page

        with mock.patch.object(re_page, 'get_redirects', side_effect=Exception("API Error")):
            result = self.task.task()
            self.assertTrue(result)
            # Should not crash

    def test_sortkey_copied_to_all_articles(self):
        """Test that sortkey is copied to all articles when there are multiple."""
        self.page_mock.title_str = "RE:Ἀβαριᾶται"
        self.page_mock.text = """{{REDaten
|BAND=I,1
}}
text article 1.
{{REAutor|OFF}}
{{REDaten
|BAND=I,2
}}
text article 2.
{{REAutor|OFF}}
{{REDaten
|BAND=II,1
}}
text article 3.
{{REAutor|OFF}}"""

        # Mock redirect page
        redirect_mock = mock.Mock(spec=pywikibot.Page)
        redirect_mock.title.return_value = "RE:Abariatai"

        re_page = RePage(self.page_mock)
        self.task.re_page = re_page

        # Verify we have 3 articles
        self.assertEqual(3, len(re_page.splitted_article_list))

        with mock.patch.object(re_page, 'get_redirects', return_value=[redirect_mock]):
            result = self.task.task()
            self.assertTrue(result)
            # Check that SORTIERUNG was set in ALL articles
            for article in re_page.splitted_article_list:
                self.assertEqual("Abariatai", article[0]["SORTIERUNG"].value)
