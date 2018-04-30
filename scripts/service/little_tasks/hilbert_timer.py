import re
from datetime import datetime

from pywikibot import Page, Site
from tools import make_html_color
from tools.catscan import PetScan
from tools.bots import OneTimeBot


class HilbertTimer(OneTimeBot):
    @staticmethod
    def get_count():
        searcher = PetScan()
        searcher.add_positive_category("David Hilbert Gesammelte Abhandlungen Erster Band")
        searcher.add_positive_category("Unkorrigiert")
        searcher.add_namespace("Seite")
        return len(searcher.run())

    @staticmethod
    def get_days_to_end_of_2018():  # pragma: no cover
        today = datetime.now()
        end_of_year = datetime(year=2018, month=12, day=31)
        return (end_of_year - today).days

    @classmethod
    def replace_in_page(cls, text: str):
        pages_per_day = cls.get_count() / cls.get_days_to_end_of_2018()
        red = make_html_color(1.0, 0.3, pages_per_day)
        green = make_html_color(0.3, 1.0, pages_per_day)
        replacement = "<!--Hilbert--> Hilbert <span style=\"background:#" \
                      "{red}{green}00\" > {pages_per_day:05.3f}" \
                      "</span> <!--Hilbert-->".format(red=red, green=green,
                                                      pages_per_day=pages_per_day)
        return re.sub("<!--Hilbert-->.*?<!--Hilbert-->", replacement, text)

    def task(self):  # pragma: no cover
        page = Page(self.wiki, "Benutzer:THE IT/Werkstatt")
        new_text = self.replace_in_page(page.text)
        page.text = new_text
        if not self.debug:
            page.save("Time is ticking")


if __name__ == "__main__":  # pragma: no cover
    WS_WIKI = Site(code='de', fam='wikisource', user='THEbotIT')
    with HilbertTimer(wiki=WS_WIKI, debug=False, log_to_screen=False, log_to_wiki=False) as bot:
        bot.run()
