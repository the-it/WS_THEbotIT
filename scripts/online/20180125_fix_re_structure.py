# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from datetime import timedelta
import re
from unittest import TestCase

from pywikibot import Page, Site

from tools.bots import OneTimeBot
from tools.catscan import PetScan


class FixReStructure(OneTimeBot):
    bot_name = '20180125_FixReStructure'

    def __init__(self, wiki, debug):
        OneTimeBot.__init__(self, wiki, debug)
        self.searcher = PetScan()
        self.timeout = timedelta(hours=5)

    def get_lemmas(self):
        self.searcher.add_positive_category("RE:Verweisung")
        self.searcher.add_no_template("REAutor")
        self.searcher.add_yes_template("REDaten")
        self.searcher.set_sort_criteria("size")
        self.searcher.set_sortorder_decending()
        for lemma in self.searcher.run():
            yield Page(self.wiki, lemma['title'])

    @staticmethod
    def process_text(text):
        regex_anmerkungen = re.compile("\s*== Anmerkungen")
        if regex_anmerkungen.search(text):
            return regex_anmerkungen.sub("\n{{REAutor|OFF}}\n== Anmerkungen", text).rstrip()
        else:
            return text.rstrip() + "\n{{REAutor|OFF}}"

    def task(self):
        for idx, page in enumerate(self.get_lemmas()):
            self.logger.info(str(idx) + "/" + str(page))
            pre_text = page.text
            page.text = self.process_text(pre_text)
            if pre_text != page.text:
                page.save("Inserted a REAutor statement for a correct structure")
            if self._watchdog():
                self.logger.warning("Enough for the day, don't run to long.")
                return False
        return True


class TestConverter(TestCase):
    def test_parse_text_without_comment(self):
        text = """{{REDaten
|BAND=I A,1
}}
Abba.

[[Kategorie:RE:Verweisung]]"""
        expected_text = """{{REDaten
|BAND=I A,1
}}
Abba.

[[Kategorie:RE:Verweisung]]
{{REAutor|OFF}}"""
        self.assertEqual(expected_text, FixReStructure.process_text(text))

    def test_parse_text_with_whitspace(self):
        text = """{{REDaten
|BAND=I A,1
}}
Abba.

[[Kategorie:RE:Verweisung]]

"""
        expected_text = """{{REDaten
|BAND=I A,1
}}
Abba.

[[Kategorie:RE:Verweisung]]
{{REAutor|OFF}}"""
        self.assertEqual(expected_text, FixReStructure.process_text(text))

    def test_parse_text_with_comment(self):
        text = """{{REDaten
|BAND=I A,1
}}
Abba.

[[Kategorie:RE:Verweisung]]

== Anmerkungen (Wikisource) ==
{{References||WS}}
"""
        expected_text = """{{REDaten
|BAND=I A,1
}}
Abba.

[[Kategorie:RE:Verweisung]]
{{REAutor|OFF}}
== Anmerkungen (Wikisource) ==
{{References||WS}}"""
        self.assertEqual(expected_text, FixReStructure.process_text(text))


if __name__ == "__main__":
    wiki = Site(code='de', fam='wikisource', user='THEbotIT')
    with FixReStructure(wiki=wiki, debug=True) as bot:
        bot.run()
        