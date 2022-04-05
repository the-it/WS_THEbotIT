import datetime

import pywikibot

from service.ws_re import public_domain
from service.ws_re.register.authors import Authors
from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.template.article import Article
from tools.bots.pi import WikiLogger


class PDKSTask(ReScannerTask):
    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)
        self.authors = Authors()
        current_year = datetime.datetime.now().year
        self.pd_todesjahr, self.pd_geburtsjahr = \
            current_year - public_domain.YEARS_AFTER_DEATH, current_year - public_domain.YEARS_AFTER_BIRTH

    def task(self):
        for re_article in self.re_page:
            if isinstance(re_article, Article):
                if re_article["KEINE_SCHÖPFUNGSHÖHE"].value:
                    if todesjahr := re_article["TODESJAHR"].value:
                        if int(todesjahr) <= self.pd_todesjahr:
                            re_article["TODESJAHR"].value = ""
                            re_article["KEINE_SCHÖPFUNGSHÖHE"].value = False
                    if geburtsjahr := re_article["GEBURTSJAHR"].value:
                        if int(geburtsjahr) <= self.pd_geburtsjahr:
                            re_article["GEBURTSJAHR"].value = ""
                            re_article["KEINE_SCHÖPFUNGSHÖHE"].value = False
