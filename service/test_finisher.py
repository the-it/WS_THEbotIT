from unittest import TestCase, mock

from pywikibot import Page, Site
from testfixtures import compare

from service.finisher import Finisher
from tools.test import real_wiki_test


class TestFinisher(TestCase):
    def setUp(self):
        self.wiki = Site(code="de", fam="wikisource", user="THEbotIT")
        self.finisher = Finisher(wiki=self.wiki)

    def tearDown(self):
        mock.patch.stopall()

    @real_wiki_test
    def test__get_checked_lemmas_from_current_pages(self):
        has_korrigiert_mock = mock.patch("service.finisher.has_korrigiert_category").start()
        def side_effect(arg: Page) -> bool:
            if arg.title() == "MKL1888:Lyck":
                return False
            return True
        has_korrigiert_mock.side_effect = side_effect
        list_of_pages = ["Seite:Meyers b11 s0001.jpg", "Seite:Meyers b11 s0002.jpg"]
        expected_lemmas = [
            ':MKL1888:Luzŭla', ':MKL1888:Luzzāra', ':MKL1888:Lwow', ':MKL1888:LXX', ':MKL1888:Lyǟos', ':MKL1888:Lycée',
            ':MKL1888:Lycēum', ':MKL1888:Lychen', ':MKL1888:Lychnis', ':MKL1888:Lychnītis', ':MKL1888:Lycīn',
            ':MKL1888:Lycĭum', ':MKL1888:Lycopérdon', ':MKL1888:Lycopersĭcum', ':MKL1888:Lycopodinae',
            ':MKL1888:Lycopodĭum'
        ]
        compare(expected_lemmas, self.finisher._get_checked_lemmas_from_current_pages(list_of_pages))

    @real_wiki_test
    def test_all_pages_fertig(self):
        only_fertig_pages = [
            Page(self.wiki, "Seite:GN.A.250 Gemein-Nachrichten 1788,5.pdf/505"),
            Page(self.wiki, "Seite:GN.A.250 Gemein-Nachrichten 1788,5.pdf/506"),
        ]
        one_korrigiert_page = [
            Page(self.wiki, "Seite:GN.A.250 Gemein-Nachrichten 1788,5.pdf/505"),
            Page(self.wiki, "Seite:GN.A.250 Gemein-Nachrichten 1788,5.pdf/506"),
            Page(self.wiki, "Seite:GN.A.250 Gemein-Nachrichten 1788,5.pdf/507"),
        ]
        proofread_pages_set = {
            "GN.A.250 Gemein-Nachrichten 1788,5.pdf/505",
            "GN.A.250 Gemein-Nachrichten 1788,5.pdf/506",
        }
        compare(True, self.finisher.all_pages_fertig(only_fertig_pages, proofread_pages_set))
        compare(False, self.finisher.all_pages_fertig(one_korrigiert_page, proofread_pages_set))

    @real_wiki_test
    def test_is_overview_page(self):
        compare(True, self.finisher.is_overview_page(Page(self.wiki, "Mathematische Principien der Naturlehre")))
        compare(False,
                self.finisher.is_overview_page(
                    Page(self.wiki,
                         "Der Ausdruck der Gemüthsbewegungen bei dem Menschen und den Thieren/Zwölftes Capitel")))

