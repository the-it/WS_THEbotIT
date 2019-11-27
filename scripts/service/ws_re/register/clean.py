import copy
from typing import Set, List

from pywikibot import Site

from scripts.service.ws_re.register.author import Authors, Author, AuthorCrawler
from scripts.service.ws_re.register.registers import Registers


class CleanAuthors:
    def __init__(self):
        self.authors = Authors()
        self.registers = Registers()

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
                mapping_set.add(mapping_value.replace("|", ""))
            elif isinstance(mapping_value, list):
                for item in mapping_value:
                    mapping_set.add(item.replace("|", ""))
            elif isinstance(mapping_value, dict):
                for item in mapping_value.values():
                    mapping_set.add(item.replace("|", ""))
        return mapping_set

    def delete_authors_without_mapping(self):
        for _ in range(2):
            author_set = self._get_deletable_authors()
            for item in sorted(author_set.difference(self._get_all_authors_from_mapping())):
                del self.authors.authors_dict[item]
        self.authors.persist()

    def delete_mappings_without_use(self):
        register_authors = set()
        for register in self.registers.volumes.values():
            for lemma in register:
                for chapter in lemma.chapters:
                    if chapter.author:
                        register_authors.add(chapter.author)
        for key in set(self.authors.authors_mapping.keys()).difference(register_authors):
            del self.authors.authors_mapping[key]
        self.authors.persist()

    def remap(self):
        for mapping in self.authors.authors_mapping:
            # key is the same linke value
            if mapping == self.authors.authors_mapping[mapping]:
                old_author_list = self.authors.get_author_by_mapping(mapping, "")
                if len(old_author_list) == 1:
                    old_author = old_author_list[0]
                    if old_author.death:
                        # now analyse if there is a better author
                        self._filter_and_replace(old_author)
        self.authors.persist()

    def _filter_and_replace(self, old_author: Author):
        new_candidates = self._create_candidates(old_author)
        if len(new_candidates) > 1:
            new_candidates = self._filter_candidates(new_candidates, old_author)
            print(old_author.name)
            print(f"  OLD: {old_author}")
            print(f"  NEW: {new_candidates}")
            if len(new_candidates) == 1:
                print(f"####{new_candidates[0].name} replace {old_author.name}")
                self.authors.set_mappings({old_author.name: new_candidates[0].name})

    def _create_candidates(self, old_author: Author) -> List[Author]:
        new_candidates = []
        for author in self.authors.authors_dict:
            if author.find(old_author.name) > -1:
                new_candidates.append(self.authors.get_author(author))
        return new_candidates

    @staticmethod
    def _filter_candidates(new_candidates: List[Author], old_author: Author) -> List[Author]:
        # eleminate old author
        new_candidates = list(filter(lambda x: x is not old_author, new_candidates))
        # eleminate dublicates
        new_candidates = list(set(new_candidates))
        # eleminate wrong death years
        if old_author.death:
            if (old_author.death % 1111) == 0:
                new_candidates = list(filter(lambda x: x.death is None, new_candidates))
            else:
                new_candidates = list(filter(lambda x: x.death == old_author.death, new_candidates))
            return new_candidates
        return []


if __name__ == "__main__":  # pragma: no cover
    cleaner = CleanAuthors()
    cleaner.remap()
    cleaner.delete_mappings_without_use()
    cleaner.delete_authors_without_mapping()
    wiki = Site(code="de", fam="wikisource", user="THEbotIT")
    cleaner.authors.set_mappings(AuthorCrawler._get_author_mapping(wiki))
    cleaner.authors.set_author(AuthorCrawler._process_author_infos(wiki))
    cleaner.authors.persist()
