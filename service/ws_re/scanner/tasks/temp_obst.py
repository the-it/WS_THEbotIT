import pywikibot

from service.ws_re.register.authors import Authors
from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.template.article import Article
from tools.bots.logger import WikiLogger


class TOBSTask(ReScannerTask):
    """
    Ernst Obst had some death problems ... correcting all fertig and korrigiert articles to Schöpfungshöhe ON
    """

    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)
        self.authors = Authors()

    def task(self):
        for article in self.re_page:
            if isinstance(article, Article):
                author_list = self.authors.get_author_by_mapping(article.author.identification, article["BAND"].value)
                if author_list and "Ernst Obst" == author_list[0].name:
                    if article["KORREKTURSTAND"].value.lower() in ["fertig", "korrigiert"]:
                        article["KEINE_SCHÖPFUNGSHÖHE"].value = True
        return True
