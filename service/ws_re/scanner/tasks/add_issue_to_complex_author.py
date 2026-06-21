import pywikibot

from service.ws_re.register.authors import Authors
from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.template.article import Article
from tools.bots.logger import WikiLogger


class AICATask(ReScannerTask):
    """
    Adds the issue (BAND) number to a ``{{REAutor}}`` reference when the author has a complex
    mapping. A mapping is complex when one author short string resolves to different authors
    depending on the issue (i.e. the entry in ``authors_mapping.json`` is a dict keyed by issue).
    Without the issue number such an author reference is ambiguous; adding it makes the reference
    resolvable on its own.
    """

    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        self.authors_mapping = Authors().authors_mapping
        super().__init__(wiki, logger, debug)

    def _has_complex_mapping(self, short_string: str) -> bool:
        return isinstance(self.authors_mapping.get(short_string), dict)

    def task(self) -> bool:
        for article in self.re_page:
            if not isinstance(article, Article):
                continue
            author = article.author
            if self._has_complex_mapping(author.short_string):
                author.issue = str(article["BAND"].value)
        return True