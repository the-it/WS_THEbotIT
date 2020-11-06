import pywikibot

from service.ws_re.template.re_page_abstract import RePageAbstract


class RePageComplex(RePageAbstract):
    def __init__(self, wiki_page: pywikibot.Page):
        super().__init__(wiki_page)

    def is_writable(self) -> bool:
        return False
