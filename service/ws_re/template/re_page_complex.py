import pywikibot

from service.ws_re.template.re_page_abstract import RePageAbstract


class RePageComplex(RePageAbstract):
    def __init__(self, wiki_page: pywikibot.Page):
        super().__init__(wiki_page)
        self.wikisource = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")
        page = pywikibot.Page(self.wikisource, "dfg")
        print(page.text)

    @property
    def is_writable(self) -> bool:
        return False
