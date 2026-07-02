"""Touch (null edit) all pages in the category 'RE:Autor nicht eindeutig bestimmbar'."""
import pywikibot

from tools.petscan import PetScan

CATEGORY = "RE:Autor nicht eindeutig bestimmbar"


def main():
    searcher = PetScan()
    searcher.add_positive_category(CATEGORY)
    lemmas = PetScan.make_plain_list(searcher.run())

    wiki = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")
    wiki.login()

    for idx, lemma in enumerate(lemmas, start=1):
        print(f"{idx}/{len(lemmas)} {lemma}")
        pywikibot.Page(wiki, title=lemma).touch()


if __name__ == "__main__":
    main()
