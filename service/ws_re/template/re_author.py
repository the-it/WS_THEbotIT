from contextlib import suppress
from dataclasses import dataclass

from tools.template_handler import TemplateHandler


@dataclass
class REAuthor:
    short_string: str
    issue: str = ""
    full_identification: str = ""

    @classmethod
    def from_template(cls, template: str):
        handler = TemplateHandler(template)
        short_string = handler.parameters[0]["value"]
        issue = ""
        full_identification = ""
        with suppress(IndexError):
            issue = handler.parameters[1]["value"]
            full_identification = handler.parameters[2]["value"]
        return cls(short_string, issue, full_identification)

    def __str__(self):
        if self.full_identification:
            return f"{{{{REAutor|{self.short_string}|{self.issue}|{self.full_identification}}}}}"
        if self.issue:
            return f"{{{{REAutor|{self.short_string}|{self.issue}}}}}"
        return f"{{{{REAutor|{self.short_string}}}}}"

