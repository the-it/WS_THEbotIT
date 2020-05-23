import re
from datetime import datetime
from typing import Tuple, List

from pywikibot import Page, Site

from tools.bots.pi import CanonicalBot
from tools.petscan import PetScan, PetscanLemma


class ReStatus(CanonicalBot):
    def __init__(self, wiki: Site, debug: bool):
        CanonicalBot.__init__(self, wiki, debug)

    def task(self) -> bool:
        fertig = self.get_sum_of_cat(["RE:Fertig"],
                                     ["RE:Teilkorrigiert", "RE:Korrigiert",
                                      "RE:Unkorrigiert", "RE:Unvollständig"])
        korrigiert = self.get_sum_of_cat(["RE:Teilkorrigiert", "RE:Korrigiert"],
                                         ["RE:Unkorrigiert", "RE:Unvollständig"])
        unkorrigiert = self.get_sum_of_cat(["RE:Unkorrigiert", "RE:Unvollständig"], [])
        self.user_page_the_it(korrigiert)
        self.history(fertig, korrigiert, unkorrigiert)
        return True

    def user_page_the_it(self, korrigiert: Tuple[int, int]):
        status_string = []

        color = make_html_color(20e6, 22e6, korrigiert[0])
        status_string.append(f"<span style=\"background:#FF{color}{color}\">{korrigiert[0]}</span>")
        color = make_html_color(5.0e3, 5.25e3, korrigiert[1])
        status_string.append(f"<span style=\"background:#FF{color}{color}\">{korrigiert[1]}</span>")

        list_of_lemmas = self.petscan(["RE:Teilkorrigiert", "RE:Korrigiert"],
                                      ["RE:Unkorrigiert", "RE:Unvollständig"])
        date_page = Page(self.wiki, list_of_lemmas[0]["title"])
        date_of_first = str(date_page.oldest_revision.timestamp)[0:10]
        gap = datetime.now() - datetime.strptime(date_of_first, "%Y-%m-%d")
        color = make_html_color(3 * 365, 3.5 * 365, gap.days)
        status_string.append(f"<span style=\"background:#FF{color}{color}\">{date_of_first}</span>")

        user_page = Page(self.wiki, "Benutzer:THE IT/Werkstatt")
        temp_text = user_page.text
        temp_text = re.sub(r"<!--RE-->.*<!--RE-->",
                           f"<!--RE-->{' ■ '.join(status_string)}<!--RE-->",
                           temp_text)
        user_page.text = temp_text
        user_page.save("todo RE aktualisiert")

    def history(self, fertig: Tuple[int, int], korrigiert: Tuple[int, int], unkorrigiert: Tuple[int, int]):
        page = Page(self.wiki, "Benutzer:THEbotIT/" + self.bot_name)
        temp_text = page.text
        composed_text = "".join(["|-\n", "|", self.timestamp.start_of_run.strftime("%Y%m%d-%H%M"),
                                 "||", str(unkorrigiert[1]), "||", str(unkorrigiert[0]),
                                 "||", str(int(unkorrigiert[0] / unkorrigiert[1])),
                                 "||", str(korrigiert[1]), "||", str(korrigiert[0]),
                                 "||", str(int(korrigiert[0] / korrigiert[1])),
                                 "||", str(fertig[1]), "||", str(fertig[0]),
                                 "||", str(int(fertig[0] / fertig[1])),
                                 "\n<!--new line-->"])
        temp_text = re.sub("<!--new line-->", composed_text, temp_text)
        page.text = temp_text
        page.save("RE Statistik aktualisiert", botflag=True)

    def get_sum_of_cat(self, cats: List[str], negacats: List[str]) -> Tuple[int, int]:
        list_of_lemmas = self.petscan(cats, negacats)
        byte_sum = 0
        for lemma in list_of_lemmas:
            byte_sum += int(lemma["len"])
        return byte_sum, len(list_of_lemmas)

    def petscan(self, categories: List[str], negative_categories: List[str]) -> List[PetscanLemma]:
        searcher = PetScan()
        for category in categories:
            searcher.add_positive_category(category)
        for neg_category in negative_categories:
            searcher.add_negative_category(neg_category)
        searcher.set_logic_union()
        self.logger.debug(str(searcher))
        return searcher.run()


if __name__ == "__main__":
    WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with ReStatus(wiki=WIKI, debug=True) as bot:
        bot.run()


def make_html_color(min_value, max_value, value):
    if max_value >= min_value:
        color = (1 - (value - min_value) / (max_value - min_value)) * 255
    else:
        color = ((value - max_value) / (min_value - max_value)) * 255
    color = max(0, min(255, color))
    return str(hex(round(color)))[2:].zfill(2).upper()
