import pywikibot

from service.ws_re.register.importer import ReImporter

WS_WIKI = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")


def analyse_tm_set():
    tm_set = ReImporter.load_tm_set()
    for article in sorted(tm_set):
        page = pywikibot.Page(WS_WIKI, f"RE:{article}")
        if not page.exists():
            print(article)


if __name__ == "__main__":
    analyse_tm_set()
