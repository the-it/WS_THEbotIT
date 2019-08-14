import json
import re
from typing import Dict, Union, Mapping, Sequence, List, Tuple

from scripts.service.ws_re.register import _REGISTER_PATH


class Author:
    def __init__(self, name: str, author_dict: Dict[str, Union[int, str]]):
        self._dict = author_dict
        if "_" in name:
            name = name.split("_")[0]
        self._name = name

    def __repr__(self):  # pragma: no cover
        return f"<{self.__class__.__name__} - name:{self.name}, birth:{self.birth}, death:{self.death}>"

    @property
    def death(self) -> Union[int, None]:
        if "death" in self._dict.keys():
            return self._dict["death"]
        return None

    @property
    def birth(self) -> Union[int, None]:
        if "birth" in self._dict.keys():
            return self._dict["birth"]
        return None

    @property
    def redirect(self) -> Union[str, None]:
        if "redirect" in self._dict.keys():
            return self._dict["redirect"]
        return None

    @property
    def name(self) -> str:
        return self._name

    def update_internal_dict(self, author_dict: Dict):
        self._dict.update(author_dict)

    def to_dict(self):
        return self._dict


class Authors:
    _REGISTER_PATH = _REGISTER_PATH

    def __init__(self):
        with open(self._REGISTER_PATH.joinpath("authors_mapping.json"), "r", encoding="utf-8") as json_file:
            self._mapping = json.load(json_file)
        self._authors = {}
        with open(self._REGISTER_PATH.joinpath("authors.json"), "r",
                  encoding="utf-8") as json_file:
            json_dict = json.load(json_file)
            for author in json_dict:
                self._authors[author] = Author(author, json_dict[author])

    def get_author_by_mapping(self, name: str, issue: str) -> Union[Author, None]:
        author = None
        try:
            mapping = self._mapping[name]
            if isinstance(mapping, dict):
                try:
                    mapping = mapping[issue]
                except KeyError:
                    mapping = mapping["*"]
            author = self.get_author(mapping)
        except KeyError:
            pass
        return author

    def get_author(self, author_key: str):
        author = self._authors[author_key.replace("|", "")]
        if author.redirect:
            author = self._authors[author.redirect]
        return author

    def set_mappings(self, mapping: Mapping):
        self._mapping.update(mapping)

    def set_author(self, mapping: Mapping):
        for author_key in mapping:
            if author_key in self._authors:
                self._authors[author_key].update_internal_dict(mapping[author_key])
            else:
                self._authors[author_key] = Author(author_key, mapping[author_key])

    def _to_dict(self):
        author_dict = dict()
        for dict_key in sorted(self._authors.keys()):
            author_dict[dict_key] = self._authors[dict_key].to_dict()
        return author_dict

    def persist(self):
        with open(self._REGISTER_PATH.joinpath("authors_mapping.json"), "w",
                  encoding="utf-8") as json_file:
            json.dump(self._mapping, json_file, sort_keys=True, indent=2, ensure_ascii=False)
        with open(self._REGISTER_PATH.joinpath("authors.json"), "w",
                  encoding="utf-8") as json_file:
            json.dump(self._to_dict(), json_file, sort_keys=True, indent=2, ensure_ascii=False)


class AuthorCrawler:
    _simple_mapping_regex = re.compile(r"\[\"([^\]]*)\"\]\s*=\s*\"([^\"]*)\"")
    _complex_mapping_regex = re.compile(r"\[\"([^\]]*)\"\]\s*=\s*\{([^\}]*)\}")

    @classmethod
    def get_mapping(cls, mapping: str) -> Dict[str, Union[str, Dict[str, str]]]:
        mapping_dict = {}
        for single_mapping in cls._split_mappings(mapping):
            mapping_dict.update(cls._extract_mapping(single_mapping))
        return mapping_dict

    @staticmethod
    def _split_mappings(mapping: str) -> Sequence[str]:
        mapping = re.sub(r"^return \{\n", "", mapping)
        mapping = re.sub(r"\}\s?$", "", mapping)
        splitted_mapping = mapping.split("\n[")
        splitted_mapping = ["[" + mapping.strip().strip(",").lstrip("[")
                            for mapping in splitted_mapping]
        return splitted_mapping

    @classmethod
    def _extract_mapping(cls, single_mapping: str) -> Dict[str, Union[str, Dict[str, str]]]:
        if "{" in single_mapping:
            return cls._extract_complex_mapping(single_mapping)
        hit = cls._simple_mapping_regex.search(single_mapping)
        return {hit.group(1): hit.group(2)}

    @classmethod
    def _extract_complex_mapping(cls, single_mapping: str) -> Dict[str, Dict[str, str]]:
        hit = cls._complex_mapping_regex.search(single_mapping)
        sub_dict = {}
        for sub_mapping in hit.group(2).split(",\n"):
            sub_hit = cls._simple_mapping_regex.search(sub_mapping)
            if sub_hit:
                sub_dict[sub_hit.group(1)] = sub_hit.group(2)
            else:

                sub_dict["*"] = sub_mapping.strip().strip("\"")
        return {hit.group(1): sub_dict}

    @classmethod
    def get_authors(cls, text: str):
        return_dict = {}
        author_list = cls._split_author_table(text)
        for author_sub_table in author_list:
            return_dict.update(cls._get_author(author_sub_table))
        return return_dict

    @staticmethod
    def _split_author_table(raw_table: str) -> List[str]:
        table = re.search(r"\{\|class=\"wikitable sortable\"\s+\|-\s+(.*)\s+\|\}",
                          raw_table, re.DOTALL).group(1)
        splitted_table = table.split("\n|-\n")
        del splitted_table[0]
        return splitted_table

    @staticmethod
    def _split_author(author_sub_table: str) -> List[str]:
        return author_sub_table.split("\n|")

    @staticmethod
    def _extract_author_name(author: str) -> Tuple[str, str]:
        author = author.lstrip("|")
        # replace all templates
        author = re.sub(r"\{\{[^\}]*\}\}", "", author)
        # if it's a link use only the second part
        if re.search(r"\[\[", author):
            author = author.split("|")[1]
        translation_dict = str.maketrans({"[": "", "]": "", "'": ""})
        author = author.translate(translation_dict)
        names = author.split(",")
        # handle funky things with a "="-character
        try:
            if "=" in names[0]:
                names[0] = names[0].split("=")[0].strip()
            if "=" in names[1]:
                names[1] = names[1].split("=")[0].strip()
        except IndexError:
            return names[0].strip(), ""
        return names[1].strip(), names[0].strip()

    @staticmethod
    def _extract_years(years: str) -> Tuple[Union[int, None], Union[int, None]]:
        hit = re.search(r"(?<!\")(\d{4})–?(\d{4})?", years)
        if hit:
            return int(hit.group(1)), int(hit.group(2)) if hit.group(2) else None
        return None, None

    @classmethod
    def _get_author(cls, author_lines: str) -> Mapping:
        lines = cls._split_author(author_lines)
        author_tuple = cls._extract_author_name(lines[0])
        years = cls._extract_years(lines[1])
        author = f"{author_tuple[0]} {author_tuple[1]}"
        author_dict = {author: {}}
        if years[0]:
            author_dict[author]["birth"] = years[0]
        if years[1]:
            author_dict[author]["death"] = years[1]
        return author_dict

    # after that get complete mapping
