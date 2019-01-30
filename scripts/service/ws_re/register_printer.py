from pywikibot import Site, Page

from scripts.service.ws_re.data_types import Registers
from tools.bots import CanonicalBot


class ReRegisterPrinter(CanonicalBot):
    def task(self):  # pragma: no cover
        registers = Registers()
        for idx, register in enumerate(registers):
            self.logger.info("Print Register {}.".format(register.volume.name))
            self.save_if_changed(Page(self.wiki,
                                      "Paulys Realencyclopädie der classischen "
                                      "Altertumswissenschaft/Register/{}/new"
                                      .format(register.volume.name)),
                                 register.get_register_str(),
                                 "Register aktualisiert")
            if idx > 6:
                break
        for idx, register in enumerate(registers.alphabetic.values()):
            self.logger.info("Print Register {}.".format(register.start))
            self.save_if_changed(Page(self.wiki,
                                      "Paulys Realencyclopädie der classischen "
                                      "Altertumswissenschaft/Register/{}/new"
                                      .format(register.start)),
                                 register.get_register_str(),
                                 "Register aktualisiert")
            if idx > 6:
                break
        return True


if __name__ == "__main__":  # pragma: no cover
    WS_WIKI = Site(code='de', fam='wikisource', user='THEbotIT')
    with ReRegisterPrinter(wiki=WS_WIKI, debug=True, log_to_wiki=False) as bot:
        bot.run()
