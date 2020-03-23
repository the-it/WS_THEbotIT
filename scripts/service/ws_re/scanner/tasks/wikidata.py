import pywikibot

from scripts.service.ws_re.scanner import ReScannerTask
from tools.bots.pi import WikiLogger


class DATATask(ReScannerTask):
    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        ReScannerTask.__init__(self, wiki, logger, debug)
        self.wikidata: pywikibot.site.DataSite = pywikibot.Site(code="wikidata", fam="wikidata", user="THEbotIT")

    def task(self):
        try:
            data_item: pywikibot.ItemPage = self.re_page.page.data_item()
        except pywikibot.NoPage:
            data_item: pywikibot.ItemPage = self.wikidata.createNewItemFromPage(page=self.re_page.page)
        self._p31(data_item)

        #data_item.save()

    def _p31(self, data_item: pywikibot.ItemPage):
        claim =  pywikibot.Claim(self.wikidata, 'P31')
        target = pywikibot.ItemPage(self.wikidata, "Q13433827")
        claim.setTarget(target)
        data_item.addClaim(claim, summary="Adding claim P31")
