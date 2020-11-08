import pywikibot

from service.ws_re.template.re_page_abstract import RePageAbstract


class RePageComplex(RePageAbstract):
    def __init__(self, wiki_page: pywikibot.Page):
        super().__init__(wiki_page)
        print(self._get_text_of_subpage("bla, bla"))
        print(self._get_text_of_subpage("bla, bla2"))

    def _get_text_of_subpage(self, page_name: str) -> str:
        return pywikibot.Page(self.page.site, page_name).text

    @property
    def is_writable(self) -> bool:
        return False
