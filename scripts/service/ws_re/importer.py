import re
from typing import Sequence, Mapping

from pywikibot import Site

from tools.bots import CanonicalBot


class ReImporter(CanonicalBot):
    def __init__(self, wiki: Site = None, debug: bool = True,
                 log_to_screen: bool = True, log_to_wiki: bool = True):
        CanonicalBot.__init__(self, wiki, debug, log_to_screen, log_to_wiki)

    def task(self):
        pass

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
        lines = match.group(1).split("|-")
        for idx, line in enumerate(lines):
            lines[idx] = line.strip()
        return lines

    @staticmethod
    def _analyse_first_column(content: str) -> Mapping:
        mapping = dict()
        match = re.search(r"\[\[RE:(.*?)\]\]", content)
        mapping["lemma"] = match.group(1)
        return mapping

    @staticmethod
    def _analyse_second_column(content: str) -> Mapping:
        mapping = dict()
        match = re.search(r"\[\[Spe.*?\|[S IXV,]*?(\d{1,4})\]\].*?\](?:-(\d{1,4}))?", content)
        mapping["start"] = int(match.group(1))
        end = match.group(2)
        mapping["end"] = end
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
        lemma_dict = {}
        lemma_dict["lemma"] = mapping_1["lemma"]
        lemma_dict["next"] = ""
        lemma_dict["previous"] = ""
        lemma_dict["redirect"] = False
        chapter_dict = {"author": author, "start": mapping_2["start"], "end": mapping_2["end"]}
        if author == "X":
            lemma_dict["redirect"] = True
            chapter_dict["author"] = ""
        if author == "?":
            chapter_dict["author"] = ""
        lemma_dict["chapters"] = list()
        lemma_dict["chapters"].append(chapter_dict)
        return lemma_dict
