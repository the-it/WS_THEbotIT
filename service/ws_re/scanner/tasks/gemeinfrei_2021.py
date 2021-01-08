import pywikibot

from service.ws_re.register.authors import Authors
from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.template.article import Article
from tools.bots.pi import WikiLogger


class GF21Task(ReScannerTask):
    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)
        self.authors = Authors()

    def task(self):
        for re_article in self.re_page:
            if isinstance(re_article, Article):
                authors = self.authors.get_author_by_mapping(re_article.author[0], re_article["BAND"].value)
                for author in authors:
                    author_string = f"{author.first_name} {author.last_name}"
                    if author_string in ("Arthur Stein", "Hugo Willrich", "Edward Capps", "August Hug"):
                        if re_article["KEINE_SCHÖPFUNGSHÖHE"].value:
                            re_article["TODESJAHR"].value = ""
                        re_article["KEINE_SCHÖPFUNGSHÖHE"].value = False
