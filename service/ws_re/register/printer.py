from pywikibot import Site, Page

from service.ws_re.register.registers import Registers
from tools import save_if_changed
from tools.bots.cloud_bot import CloudBot


def _get_simple_number_sortkey(lemma: str) -> str:
    key_list = lemma.split()
    if key_list[-1].isdigit():
        key_list[-1] = key_list[-1].zfill(3)
    return " ".join(key_list)


class ReRegisterPrinter(CloudBot):
    def __init__(self, wiki: Site = None, debug: bool = True,
                 log_to_screen: bool = True, log_to_wiki: bool = True):
        super().__init__(wiki, debug, log_to_screen, log_to_wiki)
        self.registers = Registers()

    def task(self):
        self._print_volume()
        self._print_alphabetic()
        self._print_author()
        self._print_short()
        self._print_pd()
        self._print_sortkeys()
        return True

    def _print_author(self):
        self.logger.info("Print author register.")
        overview = ["{{Tabellenstile}}\n{|class =\"wikitable sortable tabelle-kopf-fixiert\" "
                    "style=\"text-align:right;\""
                    "\n!Autor\n!Artikel\n!colspan=\"2\"|Erschließungsgrad"]
        for register in self.registers.author:
            if register.author.last_name:
                save_if_changed(Page(self.wiki,
                                     f"Paulys Realencyclopädie der classischen "
                                     f"Altertumswissenschaft/Register/{register.author.name}"),
                                register.get_register_str(print_details=register.author.name != "Hans Gärtner"),
                                "Register aktualisiert")
                overview.append(register.overview_line)
        overview.append("|}")
        save_if_changed(Page(self.wiki,
                             "Paulys Realencyclopädie der classischen "
                             "Altertumswissenschaft/Register/Autorenübersicht"),
                        "\n".join(overview),
                        "Register aktualisiert")

    def _print_alphabetic(self):
        self.logger.info("Print alphabetic register.")
        for register in self.registers.alphabetic:
            self.logger.debug(str(register))
            save_if_changed(Page(self.wiki,
                                 f"Paulys Realencyclopädie der classischen "
                                 f"Altertumswissenschaft/Register/{register.start}"),
                            register.get_register_str(),
                            "Register aktualisiert")

    def _print_pd(self):
        self.logger.info("Print public domain register.")
        for register in self.registers.pd:
            self.logger.debug(str(register))
            save_if_changed(Page(self.wiki,
                                 f"Paulys Realencyclopädie der classischen "
                                 f"Altertumswissenschaft/Register/PD {register.year}"),
                            register.get_register_str(),
                            "Register aktualisiert")

    def _print_short(self):
        self.logger.info("Print short register.")
        for register in self.registers.short:
            self.logger.debug(str(register))
            save_if_changed(Page(self.wiki,
                                 f"Paulys Realencyclopädie der classischen "
                                 f"Altertumswissenschaft/Register/{register.main_issue} kurz"),
                            register.get_register_str(),
                            "Register aktualisiert")

    def _print_volume(self):
        self.logger.info("Print volume register.")
        for register in self.registers.volumes.values():
            self.logger.debug(str(register))
            save_if_changed(Page(self.wiki,
                                 f"Paulys Realencyclopädie der classischen "
                                 f"Altertumswissenschaft/Register/{register.volume.name}"),
                            register.get_register_str(print_details=register.volume.name != "R"),
                            "Register aktualisiert")

    def _print_sortkeys(self):
        self.logger.info("Print sortkeys mapping.")
        save_if_changed(Page(self.wiki,
                             "Modul:RE/Sortierschlüssel"),
                        self._get_sortkey_map(),
                        "Sortierschlüssel aktualisiert")

    def _get_sortkey_map(self):
        sortkey_dict: dict[str, str] = {}
        for register in self.registers.volumes.values():
            for lemma in register.lemmas:
                processed_sortkey = lemma.get_sort_key()
                simple_sortkey = lemma.lemma.lower()
                if not lemma.sort_key:
                    if processed_sortkey != _get_simple_number_sortkey(simple_sortkey):
                        sortkey_dict[lemma.lemma] = processed_sortkey
        lines: list[str] = []
        for key, value in sortkey_dict.items():
            lines.append(f"[\"{key}\"] = \"{value}\",")
        sortkey_str = f"return {{\n{'\n'.join(lines)}\n}}"
        return sortkey_str


if __name__ == "__main__":  # pragma: no cover
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with ReRegisterPrinter(wiki=WS_WIKI, debug=True, log_to_wiki=False) as bot:
        bot.run()
