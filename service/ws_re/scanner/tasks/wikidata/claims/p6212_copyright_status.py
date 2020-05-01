from typing import List

from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory, \
    JsonClaimDict, SnakParameter

import pywikibot


class PublicDomainClaims():
    _COPYRIGHT_STATUS = "P6216"
    _PUBLIC_DOMAIN = "Q19652"

    _APPLIES_TO_JURISDICTION = "P1001"
    _DETERMINATION_METHOD = "P459"

    _UNITED_STATES_OF_AMERICA = "Q30"
    _PUBLISHED_MORE_THAN_THAN_95_YEARS_AGO = "Q47246828"

    _50_YEARS_AFTER_AUTHORS_DEATH = "Q29870405"
    _COUNTRIES_WITH_50_YEARS_PMA_OR_SHORTER = "Q59621182"

    _70_YEARS_AFTER_AUTHORS_DEATH = "Q29870196"
    _COUNTRIES_WITH_70_YEARS_PMA_OR_SHORTER = "Q59542795"

    _80_YEARS_AFTER_AUTHORS_DEATH = "Q29940641"
    _COUNTRIES_WITH_80_YEARS_PMA_OR_SHORTER = "Q61830521"

    _100_YEARS_AFTER_AUTHORS_DEATH = "Q29940705"
    _COUNTRIES_WITH_100_YEARS_PMA_OR_SHORTER = "Q60332278"

    _THRESHOLD_OF_ORIGINALITY = "Q707401"

    def __init__(self, wikidata: pywikibot.Site):
        self.wikidata = wikidata
        self._public_domain_item = pywikibot.ItemPage(self.wikidata, self._PUBLIC_DOMAIN)
        self.CLAIM_PUBLISHED_95_YEARS_AGO = self._init_published_more_than_95_years_ago()
        self.CLAIM_COUNTRIES_WITH_50_YEARS_PMA_OR_SHORTER = self._init_xx_years_after_authors_death(50)
        self.CLAIM_COUNTRIES_WITH_70_YEARS_PMA_OR_SHORTER = self._init_xx_years_after_authors_death(70)
        self.CLAIM_COUNTRIES_WITH_80_YEARS_PMA_OR_SHORTER = self._init_xx_years_after_authors_death(80)
        self.CLAIM_COUNTRIES_WITH_100_YEARS_PMA_OR_SHORTER = self._init_xx_years_after_authors_death(100)
        self.CLAIM_THRESHOLD_OF_ORIGINALITY = self._init_threshold_of_originality()

    def _init_published_more_than_95_years_ago(self) -> pywikibot.Claim:
        claim = pywikibot.Claim(self.wikidata, self._COPYRIGHT_STATUS)
        claim.setTarget(self._public_domain_item)
        qualifier_jurisdiction = pywikibot.Claim(self.wikidata, self._APPLIES_TO_JURISDICTION)
        target_jurisdiction = pywikibot.ItemPage(self.wikidata, self._UNITED_STATES_OF_AMERICA)
        qualifier_jurisdiction.setTarget(target_jurisdiction)
        qualifier_determination = pywikibot.Claim(self.wikidata, self._DETERMINATION_METHOD)
        target_determination = pywikibot.ItemPage(self.wikidata, self._PUBLISHED_MORE_THAN_THAN_95_YEARS_AGO)
        qualifier_determination.setTarget(target_determination)
        claim.addQualifier(qualifier_jurisdiction)
        claim.addQualifier(qualifier_determination)
        return claim

    def _init_xx_years_after_authors_death(self, years) -> pywikibot.Claim:
        claim = pywikibot.Claim(self.wikidata, self._COPYRIGHT_STATUS)
        claim.setTarget(self._public_domain_item)
        qualifier_jurisdiction = pywikibot.Claim(self.wikidata, self._APPLIES_TO_JURISDICTION)
        target_jurisdiction = pywikibot.ItemPage(self.wikidata,
                                                 getattr(self, f"_COUNTRIES_WITH_{years}_YEARS_PMA_OR_SHORTER"))
        qualifier_jurisdiction.setTarget(target_jurisdiction)
        qualifier_determination = pywikibot.Claim(self.wikidata, self._DETERMINATION_METHOD)
        target_determination = pywikibot.ItemPage(self.wikidata, getattr(self, f"_{years}_YEARS_AFTER_AUTHORS_DEATH"))
        qualifier_determination.setTarget(target_determination)
        claim.addQualifier(qualifier_jurisdiction)
        claim.addQualifier(qualifier_determination)
        return claim

    def _init_threshold_of_originality(self) -> pywikibot.Claim:
        claim = pywikibot.Claim(self.wikidata, self._COPYRIGHT_STATUS)
        claim.setTarget(self._public_domain_item)
        qualifier_determination = pywikibot.Claim(self.wikidata, self._DETERMINATION_METHOD)
        target_determination = pywikibot.ItemPage(self.wikidata, self._THRESHOLD_OF_ORIGINALITY)
        qualifier_determination.setTarget(target_determination)
        claim.addQualifier(qualifier_determination)
        return claim

    def p6216(self) -> List[pywikibot.Claim]:

        claim_list: List[pywikibot.Claim] = []
        if self._current_year - int(self._volume_of_first_article.year) > 95:
            claim_list.append(self._public_domain_claims.CLAIM_PUBLISHED_95_YEARS_AGO)
        pma_claim = self._6216_min_years_since_death
        if pma_claim:
            claim_list.append(pma_claim)
        if self._first_article["KEINE_SCHÖPFUNGSHÖHE"].value:
            claim_list.append(self._public_domain_claims.CLAIM_THRESHOLD_OF_ORIGINALITY)
        return claim_list

    @property
    def _6216_min_years_since_death(self) -> Optional[pywikibot.Claim]:
        max_death_year = 0
        for author in self._authors_of_first_article:
            if not author.death:
                max_death_year = self._current_year
            elif author.death > max_death_year:
                max_death_year = author.death
        years_since_death = self._current_year - max_death_year
        if years_since_death > 100:
            return self._public_domain_claims.CLAIM_COUNTRIES_WITH_100_YEARS_PMA_OR_SHORTER
        if years_since_death > 80:
            return self._public_domain_claims.CLAIM_COUNTRIES_WITH_80_YEARS_PMA_OR_SHORTER
        if years_since_death > 70:
            return self._public_domain_claims.CLAIM_COUNTRIES_WITH_70_YEARS_PMA_OR_SHORTER
        if years_since_death > 50:
            return self._public_domain_claims.CLAIM_COUNTRIES_WITH_50_YEARS_PMA_OR_SHORTER
        return None





class P6212CopyrightStatus(ClaimFactory):
    """
    Returns the Claim **copyright status** ->
    **<public domain statements dependend on publication age and death of author>**
    """

    _COPYRIGHT_STATUS = "P6216"
    _PUBLIC_DOMAIN = "Q19652"

    _APPLIES_TO_JURISDICTION = "P1001"
    _DETERMINATION_METHOD = "P459"

    _UNITED_STATES_OF_AMERICA = "Q30"
    _PUBLISHED_MORE_THAN_THAN_95_YEARS_AGO = "Q47246828"

    _50_YEARS_AFTER_AUTHORS_DEATH = "Q29870405"
    _COUNTRIES_WITH_50_YEARS_PMA_OR_SHORTER = "Q59621182"

    _70_YEARS_AFTER_AUTHORS_DEATH = "Q29870196"
    _COUNTRIES_WITH_70_YEARS_PMA_OR_SHORTER = "Q59542795"

    _80_YEARS_AFTER_AUTHORS_DEATH = "Q29940641"
    _COUNTRIES_WITH_80_YEARS_PMA_OR_SHORTER = "Q61830521"

    _100_YEARS_AFTER_AUTHORS_DEATH = "Q29940705"
    _COUNTRIES_WITH_100_YEARS_PMA_OR_SHORTER = "Q60332278"

    _THRESHOLD_OF_ORIGINALITY = "Q707401"

    def _get_claim_json(self) -> List[JsonClaimDict]:
        claim_list: List[pywikibot.Claim] = []
        if self._current_year - int(self._volume_of_first_article.year) > 95:
            claim_list.append(self._public_domain_claims.CLAIM_PUBLISHED_95_YEARS_AGO)
        pma_claim = self._6216_min_years_since_death
        if pma_claim:
            claim_list.append(pma_claim)
        if self._first_article["KEINE_SCHÖPFUNGSHÖHE"].value:
            claim_list.append(self._public_domain_claims.CLAIM_THRESHOLD_OF_ORIGINALITY)
        return claim_list



        start = str(self._first_article["SPALTE_START"].value)
        end: str = ""
        if self._first_article["SPALTE_END"].value not in ("", "OFF"):
            end = str(self._first_article["SPALTE_END"].value)
        columns = start
        if end and start != end:
            columns = f"{start}–{end}"
        snak = SnakParameter(property_str=self.get_property_string(),
                             target_type="string",
                             target=columns)
        return [self.create_claim_json(snak)]
