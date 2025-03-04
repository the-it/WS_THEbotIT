import os
from unittest import skipUnless, mock

REAL_DATA_TEST = "WS_REAL_DATA" in os.environ
REAL_WIKI_TEST = "WS_REAL_WIKI" in os.environ
REAL_WIKI_PART = 0
if "WS_REAL_WIKI_PART" in os.environ:
    REAL_WIKI_PART = int(os.environ["WS_REAL_WIKI_PART"])
REAL_WIKI_PARTITIONS = 1
if "WS_REAL_WIKI_PARTITIONS" in os.environ:
    REAL_WIKI_PARTITIONS = int(os.environ["WS_REAL_WIKI_PARTITIONS"])


def real_wiki_test(func):
    wrapper = skipUnless(REAL_WIKI_TEST, "only execute in test against real wiki")(func)
    if REAL_WIKI_PARTITIONS > 1:
        wrapper = skipUnless(REAL_WIKI_TEST and abs(hash(func.__name__)) % REAL_WIKI_PARTITIONS == REAL_WIKI_PART,
                             "test run in another partition")(func)
    return wrapper


class PageMock(mock.MagicMock):
    text: str = ""
    title_str: str = ""

    def title(self):
        return self.title_str


class SearchStringChecker:
    def __init__(self, search_string: str):
        self.search_string = search_string

    def is_part_of_searchstring(self, part: str):
        pre_length = len(self.search_string)
        self.search_string = "".join(self.search_string.split(part))
        return pre_length != len(self.search_string)

    def is_empty(self):
        return len(self.search_string) == 0
