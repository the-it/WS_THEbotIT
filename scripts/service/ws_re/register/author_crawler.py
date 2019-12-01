import re
from typing import List, Dict, Tuple, Optional

from pywikibot import Site

from scripts.service.ws_re.register.author import CrawlerDict, AuthorDict
from tools import fetch_text_from_wiki_site

TRANS_DICT = str.maketrans({"[": "", "]": "", "'": ""})


class AuthorCrawler:
    _SIMPLE_REGEX_MAPPING = re.compile(r"\[\"([^\]]*)\"\]\s*=\s*\"([^\"]*)\"")
    _COMPLEX_REGEX_MAPPING = re.compile(r"\[\"([^\]]*)\"\]\s*=\s*\{([^\}]*)\}")

    @classmethod
    def get_mapping(cls, mapping: str) -> CrawlerDict:
        mapping_dict = {}
        for single_mapping in cls._split_mappings(mapping):
            mapping_dict.update(cls._extract_mapping(single_mapping))
        return mapping_dict

    @staticmethod
    def _split_mappings(mapping: str) -> List[str]:
        mapping = re.sub(r"^return \{\n", "", mapping)
        mapping = re.sub(r"\}\s?$", "", mapping)
        splitted_mapping = mapping.split("\n[")
        splitted_mapping = ["[" + mapping.strip().strip(",").lstrip("[")
                            for mapping in splitted_mapping]
        return splitted_mapping

    @classmethod
    def _extract_mapping(cls, single_mapping: str) -> CrawlerDict:
        if "{" in single_mapping:
            return cls._extract_complex_mapping(single_mapping)
        hit = cls._SIMPLE_REGEX_MAPPING.search(single_mapping)
        if hit:
            return {hit.group(1): hit.group(2)}
        raise ValueError(f"{single_mapping} don't compatible to regex.")

    @classmethod
    def _extract_complex_mapping(cls, single_mapping: str) -> CrawlerDict:
        hit = cls._COMPLEX_REGEX_MAPPING.search(single_mapping)
        if hit:
            sub_dict = {}
            for sub_mapping in hit.group(2).split(",\n"):
                sub_hit = cls._SIMPLE_REGEX_MAPPING.search(sub_mapping)
                if sub_hit:
                    sub_dict[sub_hit.group(1)] = sub_hit.group(2)
                else:

                    sub_dict["*"] = sub_mapping.strip().strip("\"")
            return {hit.group(1): sub_dict}
        raise ValueError(f"{single_mapping} not compliant to regex")

    @classmethod
    def get_authors(cls, text: str) -> Dict[str, AuthorDict]:
        return_dict = {}
        author_list = cls._split_author_table(text)
        for author_sub_table in author_list:
            return_dict.update(cls._get_author(author_sub_table))
        return return_dict

    @staticmethod
    def _split_author_table(raw_table: str) -> List[str]:
        hit = re.search(r"\{\|class=\"wikitable sortable\"\s+\|-\s+(.*)\s+\|\}",
                        raw_table, re.DOTALL)
        if hit:
            table = hit.group(1)
            splitted_table = table.split("\n|-\n")
            del splitted_table[0]
            return splitted_table
        raise ValueError(f"{raw_table} not compatible to regex.")

    @staticmethod
    def _split_author(author_sub_table: str) -> List[str]:
        return author_sub_table.split("\n|")

    @staticmethod
    def _extract_author_name(author: str) -> Tuple[str, str]:
        author = author.lstrip("|")
        # replace all templates
        author = re.sub(r"\{\{.*?\}\}", "", author)
        # replace all comments
        author = re.sub(r"<!--.*?-->", "", author)
        author = re.sub(r"<nowiki>.*?</nowiki>", "", author)
        # replace all brackets
        author = re.sub(r"\(.*?\)", "", author)
        # if it's a link use only the second part
        if re.search(r"\[\[", author):
            author = author.split("|")[1]
        author = author.translate(TRANS_DICT)
        names = author.split(",")
        # handle funky things with a "="-character
        try:
            if "=" in names[0]:
                names[0] = names[0].split("=")[0].strip()
            if "=" in names[1]:
                names[1] = names[1].split("=")[0].strip()
        except IndexError:
            return "", names[0].strip()
        return names[1].strip(), names[0].strip()

    @staticmethod
    def _extract_years(years: str) -> Tuple[Optional[int], Optional[int]]:
        hit = re.search(r"(?<!\")(\d{4})–?(\d{4})?", years)
        if hit:
            return int(hit.group(1)), int(hit.group(2)) if hit.group(2) else None
        return None, None

    @classmethod
    def _get_author(cls, author_lines: str) -> Dict[str, AuthorDict]:
        lines = cls._split_author(author_lines)
        author_tuple = cls._extract_author_name(lines[0])
        years = cls._extract_years(lines[1])
        author = f"{author_tuple[0]} {author_tuple[1]}".strip()
        author_dict: Dict[str, AuthorDict] = {author: {"last_name": author_tuple[1]}}
        if author_tuple[0]:
            author_dict[author]["first_name"] = author_tuple[0]
        birth_year = years[0]
        if birth_year:
            author_dict[author]["birth"] = birth_year
        death_year = years[1]
        if death_year:
            author_dict[author]["death"] = death_year
        return author_dict

    @classmethod
    def process_author_infos(cls, wiki: Site) -> Dict[str, AuthorDict]:
        text = fetch_text_from_wiki_site(wiki,
                                         "Paulys Realencyclopädie der classischen "
                                         "Altertumswissenschaft/Autoren")
        return cls.get_authors(text)

    @classmethod
    def get_author_mapping(cls, wiki: Site) -> CrawlerDict:
        text = fetch_text_from_wiki_site(wiki, "Modul:RE/Autoren")
        return cls.get_mapping(text)
