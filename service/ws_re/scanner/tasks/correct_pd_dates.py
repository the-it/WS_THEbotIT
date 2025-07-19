import datetime
from dataclasses import dataclass
from typing import Optional

import pywikibot

from service.ws_re import public_domain
from service.ws_re.register.authors import Authors
from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.template.article import Article
from tools.bots.cloud.logger import WikiLogger


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

    def set_year_values(self, re_article_list, years):
        first_article = re_article_list[0]
        if first_article["KEINE_SCHÖPFUNGSHÖHE"].value and years.pd <= self.current_year:
            # article is not protected anymore reset all necessary values
            first_article["KEINE_SCHÖPFUNGSHÖHE"].value = False
            first_article["GEBURTSJAHR"].value = ""
            first_article["TODESJAHR"].value = ""
        else:
            # still protected ... set values according to years object
            if ((first_article["GEBURTSJAHR"].value or first_article["TODESJAHR"].value)
                    or years.pd > self.current_year):
                first_article["GEBURTSJAHR"].value = str(years.birth) if years.birth else ""
                first_article["TODESJAHR"].value = str(years.death) if years.death else ""

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
