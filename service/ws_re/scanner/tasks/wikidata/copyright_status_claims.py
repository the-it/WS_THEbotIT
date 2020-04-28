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


if __name__ == "__main__":
    PublicDomainClaims(pywikibot.Site(code="wikidata", fam="wikidata", user="THEbotIT"))
