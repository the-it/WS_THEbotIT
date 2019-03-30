from pywikibot import Site, Page

from scripts.service.ws_re.register import Registers
from tools.bots import CanonicalBot


class ReRegisterPrinter(CanonicalBot):
    def task(self):  # pragma: no cover
        registers = Registers()
        self.logger.info("Print volume register.")
        for register in registers.volumes.values():
            self.save_if_changed(Page(self.wiki,
                                      f"Paulys Realencyclopädie der classischen "
                                      f"Altertumswissenschaft/Register/{register.volume.name}"),
                                 register.get_register_str(),
                                 "Register aktualisiert")

        self.logger.info("Print alphabetic register register.")
        for register in registers.alphabetic.values():
            self.save_if_changed(Page(self.wiki,
                                      f"Paulys Realencyclopädie der classischen "
                                      f"Altertumswissenschaft/Register/{register.start}"),
                                 register.get_register_str(),
                                 "Register aktualisiert")

        return True


if __name__ == "__main__":  # pragma: no cover
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with ReRegisterPrinter(wiki=WS_WIKI, debug=True, log_to_wiki=False) as bot:
        bot.run()
