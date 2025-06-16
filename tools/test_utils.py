from unittest import TestCase

from pywikibot import Site, Page
from testfixtures import compare

from tools.test import real_wiki_test
from tools.utils import has_fertig_category, has_korrigiert_category


class TestUtils(TestCase):
    @real_wiki_test
    def test__has_category(self):
        WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
        page = Page(WS_WIKI, "Seite:Meyers b11 s0001.jpg")
        compare(True, has_fertig_category(page))
        compare(False, has_korrigiert_category(page))
