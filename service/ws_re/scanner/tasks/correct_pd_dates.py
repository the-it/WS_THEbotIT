import datetime
from dataclasses import dataclass
from typing import Optional

import pywikibot

from service.ws_re.register.authors import Authors
from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.template.re_page import ArticleList
from tools.bots.logger import WikiLogger


@dataclass
class Years:
    birth: Optional[int] = None
    death: Optional[int] = None
    pd: int = 0


class COPDTask(ReScannerTask):
    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)
        self.authors = Authors()
        self.current_year = datetime.datetime.now().year

    def task(self):
        for re_article_list in self.re_page.splitted_article_list:
            years = self.get_max_pd_year(re_article_list)
            self.set_year_values(re_article_list, years)
        return True

    def set_year_values(self, re_article_list: ArticleList, years: Years):
        article = re_article_list[0]
        if article["KEINE_SCHÖPFUNGSHÖHE"].value and years.pd <= self.current_year:
            # article is not protected anymore reset all necessary values
            article["KEINE_SCHÖPFUNGSHÖHE"].value = False
            article["GEBURTSJAHR"].value = ""
            article["TODESJAHR"].value = ""
        else:
            # still protected ... set values according to years object
            if article["GEBURTSJAHR"].value or article["TODESJAHR"].value or years.pd > self.current_year:
                article["GEBURTSJAHR"].value = str(years.birth) if years.birth else ""
                article["TODESJAHR"].value = str(years.death) if years.death else ""

    def get_max_pd_year(self, re_article_list) -> Years:
        years = Years()
        for re_article in re_article_list:
            authors = self.authors.get_author_by_mapping(re_article.author.short_string, re_article["BAND"].value)
            for author in authors:
                if author.year_public_domain > years.pd:
                    if author.death:
                        years.birth = None
                        years.death = author.death
                        years.pd = author.year_public_domain
                    else:
                        years.birth = author.birth
                        years.death = None
                        years.pd = author.year_public_domain
        return years
