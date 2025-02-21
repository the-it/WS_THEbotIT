import re
from contextlib import suppress

import pywikibot

from tools.template_finder import TemplateFinder
from tools.template_handler import TemplateHandler


class TemplateExpansion:
    def __init__(self, raw: str, wiki: pywikibot.Site):
        self.raw = raw
        self.wiki = wiki

    def expand(self) -> str:
        text_in_flight = self.raw
        for template in ["SeitePR", "PoemPR"]:
            if f"{template}|" in text_in_flight:
                lemma_parts = self.split_by_template(text_in_flight, template)
                text_in_flight = self.replace_templates(lemma_parts, template)
        return text_in_flight

    def replace_templates(self, lemma_parts: list[str], template_handler: str) -> str:
        new_parts = []
        for part in lemma_parts:
            if template_handler in part:
                parameters = TemplateHandler(part).get_parameterlist()
                section = None
                lemma_to_insert = parameters[1]["value"]
                with suppress(IndexError):
                    section = parameters[2]["value"]
                text_to_insert = self.sanitize_included_lemma(
                    pywikibot.Page(self.wiki, f"Seite:{lemma_to_insert}").text)
                if section:
                    if match := re.search(rf"<section begin={section} ?/>(.*?)<section end={section} ?/>",
                                          text_to_insert,
                                          re.DOTALL):
                        text_to_insert = match.group(1)
                new_parts.append(text_to_insert)
            else:
                new_parts.append(part)
        return "".join(new_parts)

    @staticmethod
    def sanitize_included_lemma(text: str) -> str:
        text = re.subn("<noinclude>.*?</noinclude>", "", text, flags=re.DOTALL)[0]
        return text

    @staticmethod
    def split_by_template(text_input: str, template_name: str) -> list[str]:
        positions = TemplateFinder(text_input).get_positions(template_name)
        lemma_parts = [text_input[0:positions[0].start]]
        for idx, position in enumerate(positions):
            lemma_parts.append(position.text)
            with suppress(IndexError):
                if position.end != positions[idx + 1].start:
                    lemma_parts.append(text_input[position.end:positions[idx + 1].start])
        lemma_parts.append(text_input[positions[-1].end:])
        return lemma_parts
