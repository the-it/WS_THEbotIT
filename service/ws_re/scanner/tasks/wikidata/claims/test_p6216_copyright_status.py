# pylint: disable=protected-access
from testfixtures import compare

from service.ws_re.scanner.tasks.wikidata.claims.p6216_copyright_status import P6216CopyrightStatus
from service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import \
    BaseTestClaimFactory

COUNTRIES_WITH_50_YEARS_PMA_OR_SHORTER = 59621182
FIFTY_YEARS_OR_MORE_AFTER_AUTHORS_DEATH = 29870405
COUNTRIES_WITH_70_YEARS_PMA_OR_SHORTER = 59542795
SEVENTY_YEARS_OR_MORE_AFTER_AUTHORS_DEATH = 29870196
COUNTRIES_WITH_80_YEARS_PMA_OR_SHORTER = 61830521
EIGHTY_YEARS_OR_MORE_AFTER_AUTHORS_DEATH = 29940641
COUNTRIES_WITH_100_YEARS_PMA_OR_SHORTER = 60332278
HUNDRED_YEARS_OR_MORE_AFTER_AUTHORS_DEATH = 29940705


class TestP6216CopyrightStatus(BaseTestClaimFactory):
    PMA_CLAIM_50 = {'mainsnak':
                        {'snaktype': 'value',
                         'property': 'P6216',
                         'datatype': 'wikibase-item',
                         'datavalue':
                             {'value':
                                  {'entity-type': 'item',
                                   'numeric-id': 19652},
                              'type': 'wikibase-entityid'}},
                    'type': 'statement',
                    'rank': 'normal',
                    'qualifiers':
                        {'P1001':
                             [{'snaktype': 'value',
                               'property': 'P1001',
                               'datatype': 'wikibase-item',
                               'datavalue':
                                   {'value':
                                        {'entity-type': 'item',
                                         'numeric-id': 59621182},
                                    'type': 'wikibase-entityid'}}],
                         'P459': [{'snaktype': 'value',
                                   'property': 'P459',
                                   'datatype': 'wikibase-item',
                                   'datavalue':
                                       {'value':
                                            {'entity-type': 'item',
                                             'numeric-id': 29870405},
                                        'type': 'wikibase-entityid'}}]},
                    'qualifiers-order': ['P1001', 'P459'],
                    'references': [{'snaks':
                                        {'P143':
                                             [{'snaktype': 'value',
                                               'property': 'P143',
                                               'datatype': 'wikibase-item',
                                               'datavalue':
                                                   {'value':
                                                        {'entity-type': 'item',
                                                         'numeric-id': 15522295},
                                                    'type': 'wikibase-entityid'}}]},
                                    'snaks-order': ['P143']}]}

    def test_xx_years_after_authors_death(self):
        re_page = self._create_mock_page(text="{{REDaten|BAND=II,2}}\ntext\n{{REAutor|Escher.}}", title="RE:Atreus")
        factory = P6216CopyrightStatus(re_page, self.logger)
        claim_50 = factory.xx_years_after_authors_death(50)
        compare(self.PMA_CLAIM_50, claim_50)

    def test_min_years_since_death_pma_50(self):
        re_page = self._create_mock_page(text="{{REDaten|BAND=II,2}}\ntext\n{{REAutor|Boethius}}", title="RE:Bla")
        factory = P6216CopyrightStatus(re_page, self.logger)
        claim_50 = factory.min_years_since_death
        compare(COUNTRIES_WITH_50_YEARS_PMA_OR_SHORTER,
                claim_50["qualifiers"]["P1001"][0]["datavalue"]["value"]["numeric-id"])
        compare(FIFTY_YEARS_OR_MORE_AFTER_AUTHORS_DEATH,
                claim_50["qualifiers"]["P459"][0]["datavalue"]["value"]["numeric-id"])

    def test_min_years_since_death_pma_70(self):
        re_page = self._create_mock_page(text="{{REDaten|BAND=II,2}}\ntext\n{{REAutor|Eger.}}", title="RE:Bla")
        factory = P6216CopyrightStatus(re_page, self.logger)
        claim_70 = factory.min_years_since_death
        compare(COUNTRIES_WITH_70_YEARS_PMA_OR_SHORTER,
                claim_70["qualifiers"]["P1001"][0]["datavalue"]["value"]["numeric-id"])
        compare(SEVENTY_YEARS_OR_MORE_AFTER_AUTHORS_DEATH,
                claim_70["qualifiers"]["P459"][0]["datavalue"]["value"]["numeric-id"])

    def test_min_years_since_death_pma_80(self):
        re_page = self._create_mock_page(text="{{REDaten|BAND=II,2}}\ntext\n{{REAutor|Klingmüller.}}", title="RE:Bla")
        factory = P6216CopyrightStatus(re_page, self.logger)
        claim_80 = factory.min_years_since_death
        compare(COUNTRIES_WITH_80_YEARS_PMA_OR_SHORTER,
                claim_80["qualifiers"]["P1001"][0]["datavalue"]["value"]["numeric-id"])
        compare(EIGHTY_YEARS_OR_MORE_AFTER_AUTHORS_DEATH,
                claim_80["qualifiers"]["P459"][0]["datavalue"]["value"]["numeric-id"])

    def test_min_years_since_death_pma_100(self):
        re_page = self._create_mock_page(text="{{REDaten|BAND=II,2}}\ntext\n{{REAutor|Sauer.}}", title="RE:Bla")
        factory = P6216CopyrightStatus(re_page, self.logger)
        claim_100 = factory.min_years_since_death
        compare(COUNTRIES_WITH_100_YEARS_PMA_OR_SHORTER,
                claim_100["qualifiers"]["P1001"][0]["datavalue"]["value"]["numeric-id"])
        compare(HUNDRED_YEARS_OR_MORE_AFTER_AUTHORS_DEATH,
                claim_100["qualifiers"]["P459"][0]["datavalue"]["value"]["numeric-id"])

    def test_min_years_since_death_multiple_authors(self):
        re_page = self._create_mock_page(text="{{REDaten|BAND=II,2}}\ntext\n{{REAutor|Sauer.}}\n"
                                              "{{REAbschnitt}}\ntext\n{{REAutor|Boethius}}\n"
                                              "{{REAbschnitt}}\ntext\n{{REAutor|OFF}}\n"
                                              "{{REAbschnitt}}\ntext\n{{REAutor|Eger.}}",
                                         title="RE:Bla")
        factory = P6216CopyrightStatus(re_page, self.logger)
        claim_boethius = factory.min_years_since_death
        compare(COUNTRIES_WITH_50_YEARS_PMA_OR_SHORTER,
                claim_boethius["qualifiers"]["P1001"][0]["datavalue"]["value"]["numeric-id"])
        compare(FIFTY_YEARS_OR_MORE_AFTER_AUTHORS_DEATH,
                claim_boethius["qualifiers"]["P459"][0]["datavalue"]["value"]["numeric-id"])

    def test_min_years_since_death_no_death(self):
        re_page = self._create_mock_page(text="{{REDaten|BAND=II,2}}\ntext\n{{REAutor|Stiglitz}}",
                                         title="RE:Bla")
        factory = P6216CopyrightStatus(re_page, self.logger)
        claim_boethius = factory.min_years_since_death
        compare(None, claim_boethius)

    def test_min_years_since_death_author_not_known(self):
        re_page = self._create_mock_page(text="{{REDaten|BAND=II,2}}\ntext\n{{REAutor|Blablub}}",
                                         title="RE:Bla")
        factory = P6216CopyrightStatus(re_page, self.logger)
        claim_boethius = factory.min_years_since_death
        compare(None, claim_boethius)

    def test_only_pma_claim(self):
        re_page = self._create_mock_page(text="{{REDaten|BAND=X A}}\ntext\n{{REAutor|Boethius}}", title="RE:Bla")
        factory = P6216CopyrightStatus(re_page, self.logger)
        compare(self.PMA_CLAIM_50, factory._get_claim_json()[0])

    PUBLISHED_CLAIM = {'mainsnak':
                           {'snaktype': 'value',
                            'property': 'P6216',
                            'datatype': 'wikibase-item',
                            'datavalue':
                                {'value':
                                     {'entity-type': 'item',
                                      'numeric-id': 19652},
                                 'type': 'wikibase-entityid'}},
                       'type': 'statement',
                       'rank': 'normal',
                       'qualifiers':
                           {'P1001':
                                [{'snaktype': 'value',
                                  'property': 'P1001',
                                  'datatype': 'wikibase-item',
                                  'datavalue':
                                      {'value':
                                           {'entity-type': 'item',
                                            'numeric-id': 30},
                                       'type': 'wikibase-entityid'}}],
                            'P459':
                                [{'snaktype': 'value',
                                  'property': 'P459',
                                  'datatype': 'wikibase-item',
                                  'datavalue':
                                      {'value':
                                           {'entity-type': 'item',
                                            'numeric-id': 47246828},
                                       'type': 'wikibase-entityid'}}]},
                       'qualifiers-order': ['P1001', 'P459'],
                       'references':
                           [{'snaks':
                                 {'P143':
                                      [{'snaktype': 'value',
                                        'property': 'P143',
                                        'datatype': 'wikibase-item',
                                        'datavalue':
                                            {'value':
                                                 {'entity-type': 'item',
                                                  'numeric-id': 15522295},
                                             'type': 'wikibase-entityid'}}]},
                             'snaks-order': ['P143']}]}

    def test_published_95_years_ago(self):
        re_page = self._create_mock_page(text="{{REDaten|BAND=II,2}}\ntext\n{{REAutor|Blablub}}",
                                         title="RE:Bla")
        factory = P6216CopyrightStatus(re_page, self.logger)
        compare(self.PUBLISHED_CLAIM, factory.published_95_years_ago)

    def test_published_95_years_ago_yes(self):
        re_page = self._create_mock_page(text="{{REDaten|BAND=II,2}}\ntext\n{{REAutor|Blablub}}",
                                         title="RE:Bla")
        factory = P6216CopyrightStatus(re_page, self.logger)
        compare(self.PUBLISHED_CLAIM, factory._get_claim_json()[0])

    def test_no_at_all(self):
        re_page = self._create_mock_page(text="{{REDaten|BAND=X A}}\ntext\n{{REAutor|Blablub}}",
                                         title="RE:Bla")
        factory = P6216CopyrightStatus(re_page, self.logger)
        compare([], factory._get_claim_json())

    THRESHOLD_CLAIM = {'mainsnak':
                           {'snaktype': 'value',
                            'property': 'P6216',
                            'datatype': 'wikibase-item',
                            'datavalue':
                                {'value':
                                     {'entity-type': 'item',
                                      'numeric-id': 19652},
                                 'type': 'wikibase-entityid'}},
                       'type': 'statement',
                       'rank': 'normal',
                       'qualifiers':
                           {'P459':
                                [{'snaktype': 'value',
                                  'property': 'P459',
                                  'datatype': 'wikibase-item',
                                  'datavalue':
                                      {'value':
                                           {'entity-type': 'item',
                                            'numeric-id': 707401},
                                       'type': 'wikibase-entityid'}}]},
                       'qualifiers-order': ['P459'],
                       'references':
                           [{'snaks':
                                 {'P143':
                                      [{'snaktype': 'value',
                                        'property': 'P143',
                                        'datatype': 'wikibase-item',
                                        'datavalue':
                                            {'value':
                                                 {'entity-type': 'item',
                                                  'numeric-id': 15522295},
                                             'type': 'wikibase-entityid'}}]},
                             'snaks-order': ['P143']}]}

    def test_threshold_of_originality(self):
        re_page = self._create_mock_page(text="{{REDaten|KEINE_SCHÖPFUNGSHÖHE=ON}}\ntext\n{{REAutor|Blablub}}",
                                         title="RE:Bla")
        factory = P6216CopyrightStatus(re_page, self.logger)
        compare(self.THRESHOLD_CLAIM, factory.threshold_of_originality)

    def test_threshold_of_originality_yes(self):
        re_page = self._create_mock_page(
            text="{{REDaten|BAND=X A|KEINE_SCHÖPFUNGSHÖHE=ON}}\ntext\n{{REAutor|Blablub}}",
            title="RE:Bla")
        factory = P6216CopyrightStatus(re_page, self.logger)
        compare(self.THRESHOLD_CLAIM, factory._get_claim_json()[0])

    def test_threshold_of_originality_cross_reference(self):
        re_page = self._create_mock_page(text="{{REDaten|BAND=X A|VERWEIS=ON}}\ntext\n{{REAutor|Blablub}}",
                                         title="RE:Bla")
        factory = P6216CopyrightStatus(re_page, self.logger)
        compare(self.THRESHOLD_CLAIM, factory._get_claim_json()[0])
