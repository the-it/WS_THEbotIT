from pywikibot import Site, Page

from scripts.service.ws_re.register.registers import Registers
from tools.bots import CanonicalBot


class ReRegisterPrinter(CanonicalBot):
    LEMMA_AUTHOR_SIZE = 1000

    def __init__(self, wiki: Site = None, debug: bool = True,
                 log_to_screen: bool = True, log_to_wiki: bool = True):
        super().__init__(wiki, debug, log_to_screen, log_to_wiki)
        self.registers = Registers()

    def task(self):
        self._print_volume()
        self._print_alphabetic()
        self._print_author()
        return True

    def _print_author(self):
        self.logger.info("Print author register.")
        overview = ["{|class =\"wikitable sortable\"\n!Autor\n!Artikel"]
        for register in self.registers.author:
            if register.author.last_name:
                self.logger.debug(register)
                if len(register) >= self.LEMMA_AUTHOR_SIZE:
                    self.save_if_changed(Page(self.wiki,
                                              f"Paulys Realencyclopädie der classischen "
                                              f"Altertumswissenschaft/Register/{register.author.name}"),
                                         register.get_register_str(),
                                         "Register aktualisiert")
                    overview.append(f"|-\n"
                                    f"|data-sort-value=\"{register.author.last_name}, {register.author.first_name}\""
                                    f"|[[Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/"
                                    f"{register.author.name}|{register.author.name}]]\n"
                                    f"|data-sort-value=\"{len(register):4}\"|{len(register)}")
        overview.append("|}")
        self.save_if_changed(Page(self.wiki,
                                  f"Paulys Realencyclopädie der classischen "
                                  f"Altertumswissenschaft/Register/Autorenübersicht"),
                             "\n".join(overview),
                             "Register aktualisiert")

    def _print_alphabetic(self):
        self.logger.info("Print alphabetic register.")
        for register in self.registers.alphabetic:
            self.logger.debug(register)
            self.save_if_changed(Page(self.wiki,
                                      f"Paulys Realencyclopädie der classischen "
                                      f"Altertumswissenschaft/Register/{register.start}"),
                                 register.get_register_str(),
                                 "Register aktualisiert")

    def _print_volume(self):
        self.logger.info("Print volume register.")
        for register in self.registers.volumes.values():
            self.logger.info(register)
            self.save_if_changed(Page(self.wiki,
                                      f"Paulys Realencyclopädie der classischen "
                                      f"Altertumswissenschaft/Register/{register.volume.name}"),
                                 register.get_register_str(),
                                 "Register aktualisiert")


if __name__ == "__main__":  # pragma: no cover
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with ReRegisterPrinter(wiki=WS_WIKI, debug=True, log_to_wiki=False) as bot:
        bot.run()
