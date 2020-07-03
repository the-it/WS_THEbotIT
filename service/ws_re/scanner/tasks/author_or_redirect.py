from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.template.article import Article


class REAUTask(ReScannerTask):
    ERROR_CAT = "RE:Weder Autor noch Verweis"

    def task(self):
        for article in self.re_page:
            if isinstance(article, Article):
                if not (article.author[0] != "OFF" or article["VERWEIS"].value):
                    self.re_page.add_error_category(self.ERROR_CAT)
                    return True
        self.re_page.remove_error_category(self.ERROR_CAT)
        return True
