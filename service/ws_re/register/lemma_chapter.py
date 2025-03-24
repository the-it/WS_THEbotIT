from dataclasses import dataclass, fields
from typing import Optional

from service.ws_re.register._typing import ChapterDict


@dataclass(kw_only=True)
class LemmaChapter:
    start: int
    end: Optional[int] = None
    author: Optional[str] = None

    def to_dict(self) -> ChapterDict:
        return_dict: ChapterDict = {}
        for property in fields(self):
            if value := getattr(self, property.name, None):
                return_dict[property.name] = value
        return return_dict

    @classmethod
    def from_dict(cls, lemma_dict: ChapterDict) -> 'LemmaChapter':
        return cls(**lemma_dict)
