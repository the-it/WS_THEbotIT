# pylint: disable=protected-access
from testfixtures import compare

from service.ws_re.scanner.tasks.wikidata.claims.p6216_copyright_status import P6216CopyrightStatus
from service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import \
    BaseTestClaimFactory
from tools.test import real_wiki_test


@real_wiki_test
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
        compare(59621182, claim_50["qualifiers"]["P1001"][0]["datavalue"]["value"]["numeric-id"])
        compare(29870405, claim_50["qualifiers"]["P459"][0]["datavalue"]["value"]["numeric-id"])

    def test_min_years_since_death_pma_70(self):
        re_page = self._create_mock_page(text="{{REDaten|BAND=II,2}}\ntext\n{{REAutor|Eger.}}", title="RE:Bla")
        factory = P6216CopyrightStatus(re_page, self.logger)
        claim_70 = factory.min_years_since_death
        compare(59542795, claim_70["qualifiers"]["P1001"][0]["datavalue"]["value"]["numeric-id"])
        compare(29870196, claim_70["qualifiers"]["P459"][0]["datavalue"]["value"]["numeric-id"])

    def test_min_years_since_death_pma_80(self):
        re_page = self._create_mock_page(text="{{REDaten|BAND=II,2}}\ntext\n{{REAutor|Klingmüller.}}", title="RE:Bla")
        factory = P6216CopyrightStatus(re_page, self.logger)
        claim_80 = factory.min_years_since_death
        compare(61830521, claim_80["qualifiers"]["P1001"][0]["datavalue"]["value"]["numeric-id"])
        compare(29940641, claim_80["qualifiers"]["P459"][0]["datavalue"]["value"]["numeric-id"])

    def test_min_years_since_death_pma_100(self):
        re_page = self._create_mock_page(text="{{REDaten|BAND=II,2}}\ntext\n{{REAutor|Sauer.}}", title="RE:Bla")
        factory = P6216CopyrightStatus(re_page, self.logger)
        claim_100 = factory.min_years_since_death
        compare(60332278, claim_100["qualifiers"]["P1001"][0]["datavalue"]["value"]["numeric-id"])
        compare(29940705, claim_100["qualifiers"]["P459"][0]["datavalue"]["value"]["numeric-id"])

    def test_min_years_since_death_multiple_authors(self):
        re_page = self._create_mock_page(text="{{REDaten|BAND=II,2}}\ntext\n{{REAutor|Sauer.}}\n"
                                              "{{REAbschnitt}}\ntext\n{{REAutor|Boethius}}\n"
                                              "{{REAbschnitt}}\ntext\n{{REAutor|OFF}}\n"
                                              "{{REAbschnitt}}\ntext\n{{REAutor|Eger.}}",
                                         title="RE:Bla")
        factory = P6216CopyrightStatus(re_page, self.logger)
        claim_boethius = factory.min_years_since_death
        compare(59621182, claim_boethius["qualifiers"]["P1001"][0]["datavalue"]["value"]["numeric-id"])
        compare(29870405, claim_boethius["qualifiers"]["P459"][0]["datavalue"]["value"]["numeric-id"])

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

