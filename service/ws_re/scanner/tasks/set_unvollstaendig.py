from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.template.article import Article


class SEUVTask(ReScannerTask):
    """
    SEt UnVollständig

    All articles shall have a "Korrekturstand", this got forgotten sometimes.
    This task sets the Korrekturstand to "Unvollständig" in those cases.
    """

    def task(self):
        for article in self.re_page:
            if isinstance(article, Article):
                if not article["KORREKTURSTAND"].value:
                    article["KORREKTURSTAND"].value = "Unvollständig"
        return True
