import re
import urllib.parse
from contextlib import suppress

import pywikibot

from tools.template_finder import TemplateFinder
from tools.template_handler import TemplateHandler


class TemplateExpansion:
    def __init__(self, raw: str, wiki: pywikibot.Site):
        self.raw = raw
        self.wiki = wiki

    TAG_REGEX = re.compile(r"<pages index=\"([^\"]*)\" from=(\d{1,4}) to=(\d{1,4}) \/>")

    def expand(self) -> str:
        text_in_flight = self.raw
        while match := self.TAG_REGEX.search(text_in_flight):
            text_in_flight = self.replace_tag(match, text_in_flight)
        for template in ["SeitePR", "PoemPR", "SeiteST"]:
            if f"{template}|" in text_in_flight:
                lemma_parts = self.split_by_template(text_in_flight, template)
                text_in_flight = self.replace_templates(lemma_parts, template)
        return text_in_flight

    def replace_templates(self, lemma_parts: list[str], template_str: str) -> str:
        new_parts = []
        for part in lemma_parts:
            if template_str in part:
                parameters = TemplateHandler(part).get_parameterlist()
                section = None
                lemma_to_insert = parameters[1]["value"]
                with suppress(IndexError):
                    section = parameters[2]["value"]
                text_to_insert = self.sanitize_included_lemma(
                    pywikibot.Page(self.wiki, f"Seite:{lemma_to_insert}").text)
                if section:
                    if match := re.search(rf"<section begin=\"?{section}\"? ?/>(.*?)<section end=\"?{section}\"? ?/>",
                                          text_to_insert,
                                          re.DOTALL):
                        text_to_insert = match.group(1)
                    else:
                        # if we have a referenced section,
                        # which isn't present in the target lemma set the text_to_insert empty.
                        raise ValueError(f"Wasn't able to find complete section {section} "
                                         f"for page [https://de.wikisource.org/wiki/Seite:"
                                         f"{urllib.parse.quote(lemma_to_insert)} {lemma_to_insert}].")
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

    def replace_tag(self, match, text_in_flight: str) -> str:
        text_to_insert = ""
        for i in range(int(match.group(2)), int(match.group(3)) + 1):
            text_to_insert += self.sanitize_included_lemma(
                pywikibot.Page(self.wiki, f"Seite:{match.group(1)}/{i}").text)
        return text_in_flight[0:match.start()] + text_to_insert + text_in_flight[match.end():]
