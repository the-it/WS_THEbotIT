from collections import OrderedDict
from datetime import datetime
import os
from pathlib import Path
import re
import shutil
from typing import Sequence, Mapping

from pywikibot import Site, Page
import yaml
import yamlordereddictloader

from scripts.service.ws_re.data_types import ReVolumes
from tools import path_or_str
from tools.bots import CanonicalBot


class ReImporter(CanonicalBot):
    _register_folder = "register"

    def __init__(self, wiki: Site = None, debug: bool = True,
                 log_to_screen: bool = True, log_to_wiki: bool = True):
        CanonicalBot.__init__(self, wiki, debug, log_to_screen, log_to_wiki)
        self.new_data_model = datetime(year=2019, month=1, day=1, hour=17)
        self.folder = path_or_str(Path(__file__).parent.joinpath(self._register_folder))

    def task(self):
        re_volumes = ReVolumes()
        self.clean_deprecated_register()
        for volume in re_volumes.all_volumes:
            self.logger.info("Reading Register for {}".format(volume.name))
            old_register = Page(self.wiki, "Paulys Realencyclopädie der classischen "
                                           "Altertumswissenschaft/Register/{}".format(volume.name))
            self._dump_register(volume.file_name, old_register.text)
        return True

    def clean_deprecated_register(self):
        if not self.timestamp.last_run:
            self.remove_all_register()
        try:
            os.mkdir(self.folder)
        except FileExistsError:
            pass

    def remove_all_register(self):
        self.logger.warning("The dumped registers are outdated and must be replaced.")
        try:
            shutil.rmtree(self.folder)
        except FileNotFoundError:
            pass

    @staticmethod
    def _optimize_register(raw_register: Sequence) -> Sequence:
        new_register = list()
        entry_before = raw_register[0]
        for entry in raw_register[1:]:
            if entry_before:
                if entry["lemma"] == entry_before["lemma"]:
                    entry_before["chapters"].append(entry["chapters"][0])
                    continue
                else:
                    if entry_before:
                        new_register.append(entry_before)
            entry_before = entry
        new_register.append(entry_before)  # add last entry
        return new_register

    def _dump_register(self, volume: str, old_register: str):
        file = path_or_str(Path(__file__).parent
                           .joinpath(self._register_folder).joinpath("{}.yaml".format(volume)))
        if not os.path.isfile(file):
            self.logger.info("Dumping Register for {}".format(volume))
            new_register = self._optimize_register(self._build_register(old_register))
            with open(file, mode="w", encoding="utf-8") as yaml_file:
                yaml.dump(new_register, yaml_file, Dumper=yamlordereddictloader.Dumper,
                          default_flow_style=False, allow_unicode=True)
        else:
            self.logger.info("file already there and up to date.")

    def _split_line(self, register_line: str) -> Sequence[str]:
        splitted_lines = re.split(r"\n\|", register_line)
        for idx, line in enumerate(splitted_lines):
            splitted_lines[idx] = line.strip("|")
        if not len(splitted_lines) == 4:
            self.logger.critical(register_line)
            raise ValueError("The split of the line went wrong")
        return splitted_lines

    @staticmethod
    def _split_table(table: str) -> Sequence[str]:
        match = re.search(r"\{\|\n\|-(.*)\|\}", table, re.S)
        lines = match.group(1).split("|-\n")
        for idx, line in enumerate(lines):
            lines[idx] = line.strip()
        return lines

    @staticmethod
    def _analyse_first_column(content: str) -> Mapping:
        mapping = dict()
        match = re.search(r"\[\[RE:(.*?)\]\]", content)
        mapping["lemma"] = match.group(1)
        return mapping

    def _analyse_second_column(self, content: str) -> Mapping:
        mapping = dict()
        match = re.search(r"\[\[Spe.*?\|[SR AIXV1234,]*?(\d{1,4})\]\](?:.*?\])?(?:-(\d{1,4}))?",
                          content)
        try:
            mapping["start"] = int(match.group(1))
            end = match.group(2)
            mapping["end"] = end
        except AttributeError:
            self.logger.error("There is a problem with the second column.")
            self.logger.error(content)
            raise AttributeError
        if end:
            mapping["end"] = int(end)
        else:
            mapping["end"] = mapping["start"]
        return mapping

    def _build_lemma_from_line(self, line: str) -> Mapping:
        splitted_line = self._split_line(line)
        mapping_1 = self._analyse_first_column(splitted_line[0])
        mapping_2 = self._analyse_second_column(splitted_line[1])
        author = splitted_line[2]
        lemma_dict = OrderedDict()
        lemma_dict["lemma"] = mapping_1["lemma"]
        lemma_dict["next"] = ""
        lemma_dict["previous"] = ""
        lemma_dict["redirect"] = False
        chapter_dict = OrderedDict([("start", mapping_2["start"]),
                                    ("end", mapping_2["end"]),
                                    ("author", author)])
        if author == "X":
            lemma_dict["redirect"] = True
            chapter_dict["author"] = ""
        if author == "?":
            chapter_dict["author"] = ""
        lemma_dict["chapters"] = list()
        lemma_dict["chapters"].append(chapter_dict)
        return lemma_dict

    def _build_register(self, register_text: str) -> Sequence:
        register = list()
        splitted_lines = self._split_table(register_text)
        for line in splitted_lines:
            lemma = self._build_lemma_from_line(line)
            register.append(lemma)
        return register


if __name__ == "__main__":  # pragma: no cover
    WS_WIKI = Site(code='de', fam='wikisource', user='THEbotIT')
    with ReImporter(wiki=WS_WIKI, debug=True, log_to_wiki=False) as bot:
        bot.run()
