# pylint: disable=protected-access
import pywikibot
from testfixtures import compare

from service.ws_re.scanner.tasks.wikidata.claims.p921_main_subject import P921MainSubject
from service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import \
    BaseTestClaimFactory
from tools.test import real_wiki_test


@real_wiki_test
class TestP921MainSubject(BaseTestClaimFactory):
    def test__get_claim_json_no_linked_wikipedia_lemma(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Blub}}", title="RE:Aal")
        factory = P921MainSubject(re_page, self.logger)
        claim_json = factory._get_claim_json()
        compare(0, len(claim_json))

    def test__get_claim_json_bogus_lemma(self):
        re_page = self._create_mock_page(text="{{REDaten|\nWP=de:Blablub}}\ntext\n{{REAutor|Blub}}", title="RE:Aal")
        factory = P921MainSubject(re_page, self.logger)
        claim_json = factory._get_claim_json()
        compare(0, len(claim_json))

    def test__get_claim_json_explicite_german_lemma(self):
        re_page = self._create_mock_page(text="{{REDaten|\nWP=de:Aale}}\ntext\n{{REAutor|Blub}}", title="RE:Aal")
        factory = P921MainSubject(re_page, self.logger)
        claim_json = factory._get_claim_json()
        compare(212239, claim_json[0]["mainsnak"]["datavalue"]["value"]["numeric-id"])
        compare(15522295, claim_json[0]["references"][0]["snaks"]["P143"][0]["datavalue"]["value"]["numeric-id"])

    def test__get_claim_json_implicite_german_lemma(self):
        re_page = self._create_mock_page(text="{{REDaten|\nWP=Aale}}\ntext\n{{REAutor|Blub}}", title="RE:Aal")
        factory = P921MainSubject(re_page, self.logger)
        claim_json = factory._get_claim_json()
        compare(212239, claim_json[0]["mainsnak"]["datavalue"]["value"]["numeric-id"])

    def test__get_claim_json_other_language(self):
        re_page = self._create_mock_page(text="{{REDaten|\nWP=ja:ウナギ科}}\ntext\n{{REAutor|Blub}}", title="RE:Aal")
        factory = P921MainSubject(re_page, self.logger)
        claim_json = factory._get_claim_json()
        compare(212239, claim_json[0]["mainsnak"]["datavalue"]["value"]["numeric-id"])

    def test_get_claims_to_update_nothing_to_update(self):
        re_page = self._create_mock_page(text="{{REDaten|\nWP=de:Aale}}\ntext\n{{REAutor|Blub}}", title="RE:Aal")
        factory = P921MainSubject(re_page, self.logger)
        data_item = pywikibot.ItemPage(factory.wikidata, "Q19979634")
        add_remove = factory.get_claims_to_update(data_item)
        compare({'add': {}, 'remove': []}, add_remove)

    def test_get_claims_to_update_no_claim_found(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Blub}}", title="RE:Aal")
        factory = P921MainSubject(re_page, self.logger)
        data_item = pywikibot.ItemPage(factory.wikidata, "Q19979634")
        add_remove = factory.get_claims_to_update(data_item)
        compare({'add': {}, 'remove': []}, add_remove)

    def test_get_claims_to_update_no_old_claim_exists(self):
        re_page = self._create_mock_page(text="{{REDaten|\nWP=de:Aale}}\ntext\n{{REAutor|Blub}}", title="RE:Aal")
        factory = P921MainSubject(re_page, self.logger)
        data_item = pywikibot.ItemPage(factory.wikidata, "Q1") #  Q1 has no main_subject
        add_remove = factory.get_claims_to_update(data_item)
        compare("Q212239", add_remove["add"]["P921"][0].target.id)

    def test_get_claims_to_update_target_conflict(self):
        re_page = self._create_mock_page(text="{{REDaten|\nWP=de:Aalartige}}\ntext\n{{REAutor|Blub}}", title="RE:Aal")
        factory = P921MainSubject(re_page, self.logger)
        data_item = pywikibot.ItemPage(factory.wikidata, "Q19979634")
        add_remove = factory.get_claims_to_update(data_item)
        compare({'add': {}, 'remove': []}, add_remove)
        compare("[[Kategorie:RE:Wartung Wikidata (WD!=WS)]]", re_page[1]) #  error is persisted in re_page

    def test__get_main_subject_return_main_subject(self):
        repo = pywikibot.Site("wikidata", "wikidata", user="THEbotIT").data_repository()
        # Aal (Pauly-Wissowa) (Q19979634)
        re_item = pywikibot.ItemPage(repo, "Q19979634")
        claim = P921MainSubject._get_main_subject(re_item)
        # Anguillidae (Q212239)
        compare(212239, claim.toJSON()["mainsnak"]["datavalue"]["value"]["numeric-id"])

    def test__get_main_subject_no_main_subject(self):
        repo = pywikibot.Site("wikidata", "wikidata", user="THEbotIT").data_repository()
        # Aba 1 (Pauly-Wissowa) (Q19979638)
        re_item = pywikibot.ItemPage(repo, "Q19979638")
        claim = P921MainSubject._get_main_subject(re_item)
        self.assertIsNone(claim)
