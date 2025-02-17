import re
from contextlib import suppress
from math import ceil
from typing import Optional

from pywikibot import Page, ItemPage, Claim
from pywikibot.exceptions import NoPageError

from tools.template_finder import TemplateFinderException, TemplateFinder
from tools.template_handler import TemplateHandlerException, TemplateHandler


NUMBER_TO_MONTH = {1: "Januar",
                   2: "Februar",
                   3: "März",
                   4: "April",
                   5: "Mai",
                   6: "Juni",
                   7: "Juli",
                   8: "August",
                   9: "September",
                   10: "Oktober",
                   11: "November",
                   12: "Dezember"}

_SPACE_REGEX = re.compile(r"\s+")


class AuthorInfo:
    def __init__(self, page: Page):
        self.page = page

    def get_author_dict(self) -> dict[str, str]:
        author_dict = self.get_page_infos(self.page.text)
        self.enrich_author_dict(author_dict, self.page)
        return author_dict

    @staticmethod
    def _strip_spaces(raw_string: str):
        return _SPACE_REGEX.subn(raw_string.strip(), " ")[0]

    def get_page_infos(self, text: str) -> dict[str, str]:
        template_finder = TemplateFinder(text)
        try:
            personendaten = template_finder.get_positions("Personendaten")
        except TemplateFinderException as error:
            raise ValueError("Error in processing Personendaten template.") from error
        if len(personendaten) != 1:
            raise ValueError("No or more then one Personendaten template found.")
        template_extractor = TemplateHandler(personendaten[0]["text"])
        author_dict: dict[str, str] = {}
        self.get_single_page_info("first_name", "VORNAMEN", template_extractor, author_dict)
        self.get_single_page_info("last_name", "NACHNAME", template_extractor, author_dict)
        self.get_single_page_info("birth", "GEBURTSDATUM", template_extractor, author_dict)
        self.get_single_page_info("death", "STERBEDATUM", template_extractor, author_dict)
        self.get_single_page_info("description", "KURZBESCHREIBUNG", template_extractor, author_dict)
        self.get_single_page_info("sortkey", "SORTIERUNG", template_extractor, author_dict)
        return author_dict

    def get_single_page_info(self, info: str, template_str: str, extractor: TemplateHandler,
                             author_dict: dict[str, str]):
        try:
            template_value = self._strip_spaces(extractor.get_parameter(template_str)["value"])
        except TemplateHandlerException:
            return
        if template_value:
            author_dict[info] = template_value

    def enrich_author_dict(self, author_dict: dict[str, str], page: Page):
        with suppress(NoPageError):
            data_item = page.data_item()
            if "first_name" not in author_dict and "last_name" not in author_dict:
                author_dict.pop("first_name", None)
                author_dict.pop("last_name", None)
                claim = self.get_highest_claim(data_item, "P735")
                value = self.get_value_from_claim(claim)
                if value:
                    author_dict["first_name"] = value
                claim = self.get_highest_claim(data_item, "P734")
                value = self.get_value_from_claim(claim)
                if value:
                    author_dict["last_name"] = value
            if "birth" not in author_dict:
                claim = self.get_highest_claim(data_item, "P569")
                value = self.get_value_from_claim(claim)
                if value:
                    author_dict["birth"] = value
                else:
                    author_dict["birth"] = ""
            if "death" not in author_dict:
                claim = self.get_highest_claim(data_item, "P570")
                value = self.get_value_from_claim(claim)
                if value:
                    author_dict["death"] = value
                else:
                    author_dict["death"] = ""
            if "description" not in author_dict:
                try:
                    author_dict["description"] = data_item.get()["descriptions"]["de"]
                except KeyError:
                    author_dict["description"] = ""
        if "sortkey" not in author_dict:
            if "last_name" not in author_dict:
                sortkey = author_dict["first_name"]
            elif "first_name" not in author_dict:
                sortkey = author_dict["last_name"]
            else:
                sortkey = \
                    author_dict["last_name"] + ", " + author_dict["first_name"]
            sortkey = sortkey.replace("von ", "")
            author_dict["sortkey"] = sortkey

    @staticmethod
    def get_highest_claim(data_item: ItemPage, property_str: str) -> Optional[Claim]:
        try:
            claims: list[Claim] = data_item.text["claims"][property_str]
        except KeyError:
            return None
        filtered_claims = []
        for claim in claims:
            if claim.rank == "normal":
                filtered_claims.append(claim)
            elif claim.rank == "preferred":
                return claim
        if not filtered_claims:
            return None
        return filtered_claims[0]

    @staticmethod
    def get_value_from_claim(claim: Optional[Claim]) -> Optional[str]:
        if not claim:
            return None
        # handling first_- and last_name
        if claim.type == "wikibase-item":
            target = claim.getTarget()
            if target:
                with suppress(KeyError):
                    return str(claim.getTarget().get()["labels"]["de"])
                with suppress(KeyError):
                    return str(claim.getTarget().get()["labels"]["en"])
            return None
        # handling birth and death
        if claim.type == "time":
            claim_date = claim.getTarget()
            if not claim_date:
                date_from_claim = None
            elif claim_date.precision < 7:
                date_from_claim = None
            elif claim_date.precision < 8:
                date_from_claim = str(int(ceil(float(claim_date.year) / 100.0))) + ". Jh."
            elif claim_date.precision < 10:
                date_from_claim = str(claim_date.year)
            elif claim_date.precision < 11:
                date_from_claim = NUMBER_TO_MONTH[claim_date.month] + " " + str(claim_date.year)
            else:
                date_from_claim = f"{claim_date.day}. " \
                                  f"{NUMBER_TO_MONTH[claim_date.month]} " \
                                  f"{claim_date.year}"
            if date_from_claim:
                if re.search("-", date_from_claim):
                    date_from_claim = date_from_claim.replace("-", "") + " v. Chr."
                return date_from_claim
        return None
