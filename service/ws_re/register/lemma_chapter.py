from dataclasses import dataclass
from typing import Optional, TypedDict


class ChapterDict(TypedDict, total=False):
    author: str
    start: int
    end: int


@dataclass(kw_only=True)
class LemmaChapter:
    start: int
    end: Optional[int] = None
    author: Optional[str] = None

    def to_dict(self) -> ChapterDict:
        return_dict: ChapterDict = {"start": self.start}
        if self.end:
            return_dict["end"] = self.end
        if self.author:
            return_dict["author"] = self.author
        return return_dict

    @classmethod
    def from_dict(cls, lemma_dict: ChapterDict) -> 'LemmaChapter':
        return cls(**lemma_dict)
