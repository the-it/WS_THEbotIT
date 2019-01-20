from pywikibot import Site, Page

from scripts.service.ws_re.data_types import ReRegisters
from tools.bots import CanonicalBot


class ReRegisterPrinter(CanonicalBot):
    def task(self):  # pragma: no cover
        for idx, register in enumerate(ReRegisters()):
            self.save_if_changed(Page(self.wiki,
                                      "Paulys Realencyclopädie der classischen "
                                      "Altertumswissenschaft/Register/{}/new"
                                      .format(register.volume.name)),
                                 register.get_register_str(),
                                 "Register aktualisiert")
            if idx > 4:
                break


if __name__ == "__main__":  # pragma: no cover
    WS_WIKI = Site(code='de', fam='wikisource', user='THEbotIT')
    with ReRegisterPrinter(wiki=WS_WIKI, debug=True, log_to_wiki=False) as bot:
        bot.run()
