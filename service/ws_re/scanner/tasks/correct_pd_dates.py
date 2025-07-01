import datetime
from typing import Optional

import pywikibot

from service.ws_re import public_domain
from service.ws_re.register.authors import Authors
from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.template.article import Article
from tools.bots.cloud.logger import WikiLogger


class COPDTask(ReScannerTask):
    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)
        self.authors = Authors()
        self.current_year = datetime.datetime.now().year

    def task(self):
        for re_article_list in self.re_page.splitted_article_list:
            first_article = re_article_list[0]
            years = self.get_max_pd_year(re_article_list)
            if years["death"]:
                first_article["TODESJAHR"].value = str(years["death"])
                first_article["GEBURTSJAHR"].value = ""
            elif years["birth"]:
                first_article["TODESJAHR"].value = ""
                first_article["GEBURTSJAHR"].value = str(years["birth"])
            else:
                first_article["TODESJAHR"].value = ""
                first_article["GEBURTSJAHR"].value = ""
                first_article["KEINE_SCHÖPFUNGSHÖHE"].value = False
        return True

    def get_max_pd_year(self, re_article_list) -> dict[str, Optional[int]]:
        years: dict[str, Optional[int]] = {"birth": None, "death": None, "pd": 0}
        for re_article in re_article_list:
            if not isinstance(re_article, Article):
                continue
            authors = self.authors.get_author_by_mapping(re_article.author.short_string, re_article["BAND"].value)
            for author in authors:
                if author.year_public_domain > years["pd"]:
                    if author.death:
                        years["birth"] = None
                        years["death"] = author.death
                        years["pd"] = author.year_public_domain
                    else:
                        years["birth"] = author.birth
                        years["death"] = None
                        years["pd"] = author.year_public_domain
        return years
