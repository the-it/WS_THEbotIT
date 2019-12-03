import contextlib
import json
from functools import lru_cache
from typing import Dict, Generator, List

from scripts.service.ws_re.register.author import Author, AuthorDict
from scripts.service.ws_re.register.base import _REGISTER_PATH


class Authors:
    _REGISTER_PATH = _REGISTER_PATH

    def __init__(self):
        with open(self._REGISTER_PATH.joinpath("authors_mapping.json"), "r", encoding="utf-8") as json_file:
            self._mapping = json.load(json_file)
        self._authors: Dict[str, Author] = {}
        with open(self._REGISTER_PATH.joinpath("authors.json"), "r",
                  encoding="utf-8") as json_file:
            json_dict = json.load(json_file)
            for author in json_dict:
                self._authors[author] = Author(author, json_dict[author])

    def __iter__(self) -> Generator[Author, None, None]:
        for author in self.authors_dict.values():
            if not author.redirect:
                yield author

    @lru_cache(maxsize=1000)
    def get_author_by_mapping(self, name: str, issue: str) -> List[Author]:
        author_list = []
        with contextlib.suppress(KeyError):
            mapping = self._mapping[name]
            if isinstance(mapping, dict):
                try:
                    mapping = mapping[issue]
                except KeyError:
                    mapping = mapping["*"]
            if isinstance(mapping, str):
                mapping = [mapping]
            for item in mapping:
                author_list.append(self.get_author(item))
        return author_list

    def get_author(self, author_key: str) -> Author:
        author = self._authors[author_key.replace("|", "")]
        if author.redirect:
            author = self._authors[author.redirect]
        return author

    def set_mappings(self, mapping: Dict[str, str]):
        self._mapping.update(mapping)

    def set_author(self, mapping: Dict[str, AuthorDict]):
        for author_key in mapping:
            if author_key in self._authors:
                self._authors[author_key].update_internal_dict(mapping[author_key])
            else:
                self._authors[author_key] = Author(author_key, mapping[author_key])

    def _to_dict(self) -> Dict[str, AuthorDict]:
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

    @property
    def authors_dict(self) -> Dict[str, Author]:
        return self._authors

    @property
    def authors_mapping(self):
        return self._mapping
