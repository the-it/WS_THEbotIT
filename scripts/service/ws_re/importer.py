import re
from typing import Sequence

from pywikibot import Site

from tools.bots import CanonicalBot


class ReImporter(CanonicalBot):
    def __init__(self, wiki: Site = None, debug: bool = True,
                 log_to_screen: bool = True, log_to_wiki: bool = True):
        CanonicalBot.__init__(self, wiki, debug, log_to_screen, log_to_wiki)

    def task(self):
        pass

    @staticmethod
    def _split_line(register_line: str) -> Sequence[str]:
        splitted_lines = re.split(r"\n\|", register_line)
        for idx, line in enumerate(splitted_lines):
            splitted_lines[idx] = line.strip("|")
        return splitted_lines

    @staticmethod
    def _split_table(table: str) -> Sequence[str]:
        match = re.search(r"\{\|\n\|-(.*)\|\}", table, re.S)
        lines = match.group(1).split("|-")
        for idx, line in enumerate(lines):
            lines[idx] = line.strip()
        return lines
