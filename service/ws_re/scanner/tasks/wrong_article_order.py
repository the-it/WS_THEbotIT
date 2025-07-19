from service.ws_re.scanner.tasks.base import get_redirect
from service.ws_re.scanner.tasks.base_task import ReScannerTask


class WAORTask(ReScannerTask):
    MAINTENANCE_CAT = "RE:Artikel sind in der falschen Reihenfolge"

    def task(self):
        # just one article, nothing to check
        if len(self.re_page.splitted_article_list) == 1:
            return
        # first article isn't a VERWEIS. First article is a relevant article
        if not self.re_page.splitted_article_list.first_article["VERWEIS"].value:
            return
        # article redirects to another lemma
        if isinstance(get_redirect(self.re_page.first_article), str):
            return
        for sub_article_list in self.re_page.splitted_article_list.list[1:]:
            if not sub_article_list.daten["VERWEIS"].value and len(sub_article_list.daten.text) > 100:
                self.re_page.add_error_category(category=self.MAINTENANCE_CAT)
                break
