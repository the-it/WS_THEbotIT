import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Union

from pywikibot import Site, Page


class ToolException(Exception):
    pass


def make_html_color(min_value, max_value, value):
    if max_value >= min_value:
        color = (1 - (value - min_value) / (max_value - min_value)) * 255
    else:
        color = ((value - max_value) / (min_value - max_value)) * 255
    color = max(0, min(255, color))
    return str(hex(round(color)))[2:].zfill(2).upper()


def fetch_text_from_wiki_site(wiki: Site, lemma: str) -> str:  # pragma: no cover
    text = Page(wiki, lemma).text
    if not text:
        raise ToolException("The lemma {} is empty.".format(lemma))
    return text


if datetime.now() > datetime(year=2020, month=9, day=13):  # pragma: no cover
    raise DeprecationWarning("Python 3.5 has reached end of live. "
                             "Consider removing all the casts Path -> str.")


if sys.version_info < (3, 6):
    def path_or_str(path: Path) -> Union[Path, str]:
        return str(path)
else:
    def path_or_str(path: Path) -> Union[Path, str]:
        return path

INTEGRATION_TEST = "INTEGRATION" in os.environ
