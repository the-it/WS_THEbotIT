import contextlib
from collections import OrderedDict
from typing import Optional

from service.ws_re.register._typing import ChapterDict


class LemmaChapter:
    _keys = ["start", "end", "author"]

    def __init__(self, chapter_dict: ChapterDict):
        self._dict = chapter_dict

    def __repr__(self):  # pragma: no cover
        return f"<{self.__class__.__name__} - start:{self.start}, end:{self.end}, author:{self.author}>"

    def is_valid(self) -> bool:
        with contextlib.suppress(TypeError):
            if "start" in self._dict:
                return True
        return False

    def get_dict(self) -> ChapterDict:
        return_dict: ChapterDict = OrderedDict()  # type: ignore
        for property_key in self._keys:
            if property_key in self._dict:
                return_dict[property_key] = self._dict[property_key]  # type: ignore
        return return_dict

    @property
    def start(self) -> int:
        return self._dict["start"]

    @property
    def end(self) -> Optional[int]:
        if "end" in self._dict:
            return self._dict["end"]
        return None

    @property
    def author(self) -> Optional[str]:
        if "author" in self._dict.keys():
            return self._dict["author"]
        return None
