import json
from contextlib import suppress
from pathlib import Path
from string import Template
from typing import Dict, List

import dictdiffer

from service.ws_re.scanner.tasks.wikidata.base import get_article_type
from service.ws_re.template.re_page import RePage

PROOFREAD_BADGES = {"fertig": "Q20748093",
                    "korrigiert": "Q20748092",
                    "unkorrigiert": "Q20748091"}


class NonClaims:
    def __init__(self, re_page: RePage):
        self.re_page = re_page
        with open(Path(__file__).parent.joinpath("non_claims_article.json"), encoding="utf-8") as non_claims_json:
            self._non_claims_template_article = Template(non_claims_json.read())
        with open(Path(__file__).parent.joinpath("non_claims_crossref.json"), encoding="utf-8") as non_claims_json:
            self._non_claims_template_crossref = Template(non_claims_json.read())
        with open(Path(__file__).parent.joinpath("non_claims_index.json"), encoding="utf-8") as non_claims_json:
            self._non_claims_template_index = Template(non_claims_json.read())
        with open(Path(__file__).parent.joinpath("non_claims_prologue.json"), encoding="utf-8") as non_claims_json:
            self._non_claims_template_prologue = Template(non_claims_json.read())

    @property
    def dict(self) -> Dict:
        article_type = get_article_type(self.re_page)
        if article_type == "index":
            replaced_json = self._non_claims_template_index.substitute(lemma=self.re_page.lemma_without_prefix)
        elif article_type == "prologue":
            replaced_json = self._non_claims_template_prologue.substitute(lemma=self.re_page.lemma_without_prefix)
        elif article_type == "crossref":
            replaced_json = self._non_claims_template_crossref.substitute(lemma=self.re_page.lemma_without_prefix)
        else:
            replaced_json = self._non_claims_template_article.substitute(lemma=self.re_page.lemma_without_prefix)
        non_claims: Dict = json.loads(replaced_json)
        non_claims["sitelinks"] = {"dewikisource": {
            "site": "dewikisource",
            "title": self.re_page.lemma,
            "badges": self._proofread_badge
        }}
        return non_claims

    @property
    def _proofread_badge(self) -> List[str]:
        proofread_badge = []
        try:
            proofread_badge.append(PROOFREAD_BADGES[str(self.re_page.first_article["KORREKTURSTAND"].value).lower()])
        except KeyError:
            pass
        return proofread_badge

    def _languages(self, labels_or_descriptions: str) -> List[str]:
        return [str(language) for language in self.dict[labels_or_descriptions].keys()]

    def labels_and_sitelinks_has_changed(self, old_non_claims: Dict) -> bool:
        # claims are not relevant here
        with suppress(KeyError):
            del old_non_claims["claims"]
        # remove all languages, that are not set by this bot
        for labels_or_descriptions in ("labels", "descriptions"):
            try:
                old_non_claims[labels_or_descriptions] = {key: value
                                                          for (key, value)
                                                          in old_non_claims[labels_or_descriptions].items()
                                                          if key in self._languages(labels_or_descriptions)}
            except KeyError:
                # if there is no key, doesn't matter, the diff will show it then.
                pass
        return bool(tuple(dictdiffer.diff(self.dict, old_non_claims)))
