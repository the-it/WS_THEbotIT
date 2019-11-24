import copy
from typing import Set

from scripts.service.ws_re.register.author import Authors


class CleanAuthors:
    def __init__(self):
        self.authors = Authors()

    def _get_deletable_authors(self):
        raw_author_set = set(self.authors.authors_dict.keys())
        author_set = copy.copy(raw_author_set)
        for author in raw_author_set:
            author_obj = self.authors.authors_dict[author]
            if author_obj.redirect:
                author_set.remove(author_obj.redirect)
        return author_set

    def _get_all_authors_from_mapping(self) -> Set[str]:
        mapping_set = set()
        for mapping_key in self.authors.authors_mapping:
            mapping_value = self.authors.authors_mapping[mapping_key]
            if isinstance(mapping_value, str):
                mapping_set.add(mapping_value)
            elif isinstance(mapping_value, list):
                for item in mapping_value:
                    mapping_set.add(item)
            elif isinstance(mapping_value, dict):
                for item in mapping_value.values():
                    mapping_set.add(item)
        return mapping_set

    def delete_authors_without_mapping(self):
        for _ in range(2):
            author_set = self._get_deletable_authors()
            for item in sorted(author_set.difference(self._get_all_authors_from_mapping())):
                del self.authors.authors_dict[item]
        self.authors.persist()


if __name__ == "__main__":  # pragma: no cover
    cleaner = CleanAuthors()
    cleaner.delete_authors_without_mapping()
