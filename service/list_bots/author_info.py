import re
from contextlib import suppress
from math import ceil
from typing import Optional

from pywikibot import Page, ItemPage, Claim
from pywikibot.exceptions import NoPageError

from service.list_bots._base import get_page_infos, is_empty_value, assign_value

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


class AuthorInfo:
    PROPERTY_MAPPING = {
        "first_name": "VORNAMEN",
        "last_name": "NACHNAME",
        "birth": "GEBURTSDATUM",
        "death": "STERBEDATUM",
        "description": "KURZBESCHREIBUNG",
        "sortkey": "SORTIERUNG",
    }

    def __init__(self, page: Page):
        self.page = page

    def get_author_dict(self) -> dict[str, str]:
        author_dict = get_page_infos(self.page.text, "Personendaten", self.PROPERTY_MAPPING)
        self.enrich_author_dict(author_dict, self.page)
        return author_dict

    def enrich_author_dict(self, author_dict: dict[str, str], page: Page):
        with suppress(NoPageError):
            data_item = page.data_item()
            if is_empty_value("first_name", author_dict) and is_empty_value("last_name", author_dict):
                claim = self.get_highest_claim(data_item, "P735")
                value = self.get_value_from_claim(claim)
                assign_value("first_name", value, author_dict)
                claim = self.get_highest_claim(data_item, "P734")
                value = self.get_value_from_claim(claim)
                assign_value("last_name", value, author_dict)
            if is_empty_value("birth", author_dict):
                claim = self.get_highest_claim(data_item, "P569")
                value = self.get_value_from_claim(claim)
                assign_value("birth", value, author_dict)
            if is_empty_value("death", author_dict):
                claim = self.get_highest_claim(data_item, "P570")
                value = self.get_value_from_claim(claim)
                assign_value("death", value, author_dict)
            if is_empty_value("description", author_dict):
                try:
                    author_dict["description"] = data_item.get()["descriptions"]["de"]
                except KeyError:
                    author_dict["description"] = ""
        if is_empty_value("sortkey", author_dict):
            if is_empty_value("last_name", author_dict):
                sortkey = author_dict["first_name"]
            elif is_empty_value("first_name", author_dict):
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
