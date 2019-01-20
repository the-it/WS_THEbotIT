import json
from collections import OrderedDict
from datetime import datetime
import os
from pathlib import Path
import re
import shutil
from typing import Sequence, Dict, Tuple

from pywikibot import Site, Page

from scripts.service.ws_re.data_types import Volumes
from tools import path_or_str
from tools.bots import CanonicalBot


class ReImporter(CanonicalBot):
    _register_folder = "register"

    def __init__(self, wiki: Site = None, debug: bool = True,
                 log_to_screen: bool = True, log_to_wiki: bool = True):
        CanonicalBot.__init__(self, wiki, debug, log_to_screen, log_to_wiki)
        self.new_data_model = datetime(year=2019, month=1, day=19, hour=18)
        self.folder = path_or_str(Path(__file__).parent.joinpath(self._register_folder))
        self.authors = {}  # type: Dict[str, Dict[str, Dict[str, str]]]
        self.current_volume = ""

    def task(self):  # pragma: no cover
        re_volumes = Volumes()
        self.clean_deprecated_register()
        for volume in re_volumes.all_volumes:
            self.current_volume = volume.name
            self.logger.info("Reading Register for {}".format(volume.name))
            old_register = Page(self.wiki, "Paulys Realencyclopädie der classischen "
                                           "Altertumswissenschaft/Register/{}".format(volume.name))
            self._dump_register(volume.file_name, old_register.text)
        self._dump_authors()
        return True

    def clean_deprecated_register(self):
        # this indicates that the data was older then the timestamp in self.new_data_model
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
            if entry["lemma"] == entry_before["lemma"]:
                entry_before["chapters"].append(entry["chapters"][0])
            else:
                new_register.append(entry_before)
                entry_before = entry
        new_register.append(entry_before)  # add last entry
        return new_register

    @staticmethod
    def _add_pre_post_register(raw_register: Sequence) -> Sequence:
        new_register = list()
        len_raw_register = len(raw_register)

        for idx, entry in enumerate(raw_register):
            if idx > 0:
                entry["previous"] = raw_register[idx - 1]["lemma"]
            if idx < len_raw_register - 1:
                entry["next"] = raw_register[idx + 1]["lemma"]
            new_register.append(entry)

        del raw_register[0]["previous"]
        del raw_register[-1]["next"]
        return new_register

    def _dump_register(self, volume: str, old_register: str):
        file = path_or_str(Path(__file__).parent
                           .joinpath(self._register_folder).joinpath("{}.json".format(volume)))
        if not os.path.isfile(file):
            self.logger.info("Dumping Register for {}".format(volume))
            new_register = \
                self._add_pre_post_register(
                    self._optimize_register(
                        self._build_register(old_register)))
            with open(file, mode="w", encoding="utf-8") as json_file:
                json.dump(new_register, json_file, indent=2, ensure_ascii=False)
        else:
            self.logger.info("file already there and up to date.")

    def _dump_authors(self):
        mapping_dict = {}
        details_dict = {}
        for author in self.authors:
            details, mapping = self._create_author_detail(author)
            mapping_dict[author] = mapping
            details_dict.update(details)
        path = Path(__file__).parent.joinpath(self._register_folder)
        mapping_file = path.joinpath("authors_mapping.json")
        with open(path_or_str(mapping_file), mode="w", encoding="utf-8") as json_file:
            json.dump(mapping_dict, json_file, indent=2, sort_keys=True, ensure_ascii=False)
        details_file = path.joinpath("authors.json")
        with open(path_or_str(details_file), mode="w", encoding="utf-8") as json_file:
            json.dump(details_dict, json_file, indent=2, sort_keys=True, ensure_ascii=False)

    def _create_author_detail(self, author: str) -> Tuple[Dict, Dict]:
        author_detail = {}
        author_mapping = {}
        author_years = self._convert_author(author)
        if len(author_years) == 1:
            year = next(iter(author_years))
            author_detail = {author: {}}
            if year:
                author_detail[author].update({"death": int(year)})
            author_mapping = author
        else:
            count = ("year", 0)
            for year in author_years:
                if len(author_years[year]) > count[1]:
                    count = (year, len(author_years[year]))
            author_detail[author] = {"death": int(count[0])}
            author_mapping["*"] = author
            del author_years[count[0]]
            for year in author_years:
                for issue in author_years[year]:
                    extended_author = "{}_{}".format(author, issue)
                    author_detail[extended_author] = {}
                    author_mapping[issue] = extended_author
                    if year:
                        author_detail[extended_author].update({"death": int(year)})
        return author_detail, author_mapping

    def _convert_author(self, author: str) -> Dict:
        new_dict = {}
        for issue in self.authors[author]:
            year = self.authors[author][issue]
            if year in new_dict:
                new_dict[year].add(issue)
            else:
                new_dict[year] = set([issue])
        return new_dict

    def _register_author(self, author: str, death_year: str):
        if author not in self.authors.keys():
            self.authors[author] = {}
        if self.current_volume not in self.authors[author].keys():
            self.authors[author][self.current_volume] = death_year
        elif death_year != self.authors[author][self.current_volume]:
            if author == "Thomsen" and death_year == "4444":
                return
            self.logger.error("first author: {}, {}".format(author, self.authors[author]))
            self.logger.error("second author: {}, {}".format(author, death_year))
            raise ValueError("We have a serious problem. "
                             "There are two authors with the same name in one register.")

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
    def _analyse_first_column(content: str) -> Dict:
        mapping = dict()
        match = re.search(r"\[\[RE:(.*?)\]\]", content)
        mapping["lemma"] = match.group(1)
        return mapping

    def _analyse_second_column(self, content: str) -> Dict:
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

    def _build_lemma_from_line(self, line: str) -> Dict:
        splitted_line = self._split_line(line)
        mapping_1 = self._analyse_first_column(splitted_line[0])
        mapping_2 = self._analyse_second_column(splitted_line[1])
        author = splitted_line[2]
        year = splitted_line[3]
        lemma_dict = OrderedDict()
        lemma_dict["lemma"] = mapping_1["lemma"]
        lemma_dict["previous"] = ""
        lemma_dict["next"] = ""
        lemma_dict["redirect"] = False
        chapter_dict = OrderedDict([("start", mapping_2["start"]),
                                    ("end", mapping_2["end"]),
                                    ("author", author)])
        if author == "X":
            lemma_dict["redirect"] = True
            chapter_dict["author"] = ""
        if author == "?":
            chapter_dict["author"] = ""
        if chapter_dict["author"]:
            try:
                self._register_author(chapter_dict["author"], year)
            except ValueError as original:
                self.logger.error("author: {}, year: {}".format(chapter_dict["author"], year))
                raise original
        else:
            del chapter_dict["author"]
        if not lemma_dict["redirect"]:
            del lemma_dict["redirect"]
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
