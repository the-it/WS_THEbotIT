from pywikibot import Site, Page

from scripts.service.ws_re.register.registers import Registers
from tools.bots import CanonicalBot


class ReRegisterPrinter(CanonicalBot):
    def task(self):
        registers = Registers()
        self.logger.info("Print volume register.")
        for register in registers.volumes.values():
            self.logger.info(register)
            self.save_if_changed(Page(self.wiki,
                                      f"Paulys Realencyclopädie der classischen "
                                      f"Altertumswissenschaft/Register/{register.volume.name}"),
                                 register.get_register_str(),
                                 "Register aktualisiert")

        self.logger.info("Print alphabetic register.")
        for register in registers.alphabetic:
            self.logger.debug(register)
            self.save_if_changed(Page(self.wiki,
                                      f"Paulys Realencyclopädie der classischen "
                                      f"Altertumswissenschaft/Register/{register.start}"),
                                 register.get_register_str(),
                                 "Register aktualisiert")
        self.logger.info("Print author register.")
        for i, register in enumerate(registers.author):
            self.logger.debug(f"|-\n|{i:4}||{len(register):4}||{register.author.name}")
        return True


if __name__ == "__main__":  # pragma: no cover
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with ReRegisterPrinter(wiki=WS_WIKI, debug=True, log_to_wiki=False) as bot:
        bot.run()
