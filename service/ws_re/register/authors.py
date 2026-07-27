import contextlib
import json
from collections.abc import Generator

from service.ws_re.register._typing import AuthorDict, CrawlerDict
from service.ws_re.register.author import Author
from service.ws_re.register.repo import DataRepo


class Authors:
    def __init__(self, update_data=False):
        self.data_repo = DataRepo(update_data)
        with open(self.data_repo.get_data_path().joinpath("authors_mapping.json"), "r", encoding="utf-8") as json_file:
            self._mapping = json.load(json_file)
        self._authors: dict[str, Author] = {}
        with open(self.data_repo.get_data_path().joinpath("authors.json"), "r", encoding="utf-8") as json_file:
            json_dict = json.load(json_file)
            for author in json_dict:
                self._authors[author] = Author(author, json_dict[author])
        self._author_by_mapping_cache: dict[tuple[str, str], list[Author]] = {}

    def __iter__(self) -> Generator[Author]:
        for author in sorted(self.authors_dict.values(), key=lambda item: f"{item.last_name}, {item.first_name}"):
            if not author.redirect:
                yield author

    def get_author_by_mapping(self, name: str, issue: str) -> list[Author]:
        cache_key = (name, issue)
        with contextlib.suppress(KeyError):
            return self._author_by_mapping_cache[cache_key]
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
        self._author_by_mapping_cache[cache_key] = author_list
        return author_list

    def get_author(self, author_key: str) -> Author:
        author = self._authors[author_key.replace("|", "")]
        if author.redirect:
            author = self._authors[author.redirect]
        return author

    def set_mappings(self, mapping: CrawlerDict):
        self._mapping.update(mapping)

    def set_author(self, mapping: dict[str, AuthorDict]):
        for author_key, author_value in mapping.items():
            if author_key in self._authors:
                self._authors[author_key].update_internal_dict(author_value)
            else:
                self._authors[author_key] = Author(author_key, author_value)

    def _to_dict(self) -> dict[str, AuthorDict]:
        author_dict = {}
        for dict_key in sorted(self._authors.keys()):
            author_dict[dict_key] = self._authors[dict_key].to_dict()
        return author_dict

    def persist(self):
        with open(self.data_repo.get_data_path().joinpath("authors_mapping.json"), "w", encoding="utf-8") as json_file:
            json.dump(self._mapping, json_file, sort_keys=True, indent=2, ensure_ascii=False)
        with open(self.data_repo.get_data_path().joinpath("authors.json"), "w", encoding="utf-8") as json_file:
            json.dump(self._to_dict(), json_file, sort_keys=True, indent=2, ensure_ascii=False)

    @property
    def authors_dict(self) -> dict[str, Author]:
        return self._authors

    @property
    def authors_mapping(self):
        return self._mapping
