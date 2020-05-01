from typing import List, Optional

from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory, \
    JsonClaimDict, SnakParameter


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
        claim_list: List[JsonClaimDict] = []
        if self._current_year - int(self._volume_of_first_article.year) > 95:
            claim_list.append(self.published_95_years_ago)
        pma_claim = self.min_years_since_death
        if pma_claim:
            claim_list.append(pma_claim)
        if self._first_article["KEINE_SCHÖPFUNGSHÖHE"].value:
            claim_list.append(self.threshold_of_originality)
        return claim_list

    @property
    def published_95_years_ago(self) -> JsonClaimDict:
        qualifier_jur = SnakParameter(self._APPLIES_TO_JURISDICTION, "wikibase-item",
                                      self._UNITED_STATES_OF_AMERICA)
        qualifier_det = SnakParameter(self._DETERMINATION_METHOD, "wikibase-item",
                                      self._PUBLISHED_MORE_THAN_THAN_95_YEARS_AGO)
        claim_parameter = SnakParameter(self._COPYRIGHT_STATUS, "wikibase-item", self._PUBLIC_DOMAIN)
        claim = self.create_claim_json(claim_parameter, [qualifier_jur, qualifier_det])
        return claim

    def xx_years_after_authors_death(self, years) -> JsonClaimDict:
        qualifier_jur = SnakParameter(self._APPLIES_TO_JURISDICTION, "wikibase-item",
                                      getattr(self, f"_COUNTRIES_WITH_{years}_YEARS_PMA_OR_SHORTER"))
        qualifier_det = SnakParameter(self._DETERMINATION_METHOD, "wikibase-item",
                                      getattr(self, f"_{years}_YEARS_AFTER_AUTHORS_DEATH"))
        claim_parameter = SnakParameter(self._COPYRIGHT_STATUS, "wikibase-item", self._PUBLIC_DOMAIN)
        claim = self.create_claim_json(claim_parameter, [qualifier_jur, qualifier_det])
        return claim

    @property
    def min_years_since_death(self) -> Optional[JsonClaimDict]:
        max_death_year = 0
        for author in self._authors_of_first_article:
            if not author.death:
                max_death_year = self._current_year
            elif author.death > max_death_year:
                max_death_year = author.death
        years_since_death = self._current_year - max_death_year
        if years_since_death > 100:
            return self.xx_years_after_authors_death(100)
        if years_since_death > 80:
            return self.xx_years_after_authors_death(80)
        if years_since_death > 70:
            return self.xx_years_after_authors_death(70)
        if years_since_death > 50:
            return self.xx_years_after_authors_death(50)
        return None

    @property
    def threshold_of_originality(self) -> JsonClaimDict:
        qualifier_det = SnakParameter(self._DETERMINATION_METHOD, "wikibase-item",
                                      self._THRESHOLD_OF_ORIGINALITY)
        claim_parameter = SnakParameter(self._COPYRIGHT_STATUS, "wikibase-item", self._PUBLIC_DOMAIN)
        claim = self.create_claim_json(claim_parameter, [qualifier_det])
        return claim
