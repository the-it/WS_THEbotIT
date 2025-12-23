# pylint: disable=protected-access
import pywikibot
from pywikibot import ItemPage
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

    def test_replace_redirect(self):
        re_page = self._create_mock_page(text="{{REDaten|\nWP=de:Lethaia}}\ntext\n{{REAutor|Blub}}", title="RE:Lethaia")
        factory = P921MainSubject(re_page, self.logger)
        # Build an old claim whose target is a redirecting item
        old_claims = factory.get_old_claims(ItemPage(factory.wikidata, "Q136699843"))
        old_claims[0].target = ItemPage(factory.wikidata, "Q6533233")  # redirects to Q5973878

        new_claim = factory.replace_redirect(old_claims[0])

        # original claim must remain unchanged
        compare("Q6533233", old_claims[0].target.id)
        # returned claim must point to the redirect target
        compare("Q5973878", new_claim.target.id)

    def test_get_claims_to_update_replaces_redirect(self):
        re_page = self._create_mock_page(text="{{REDaten|\nWP=de:Lethaia}}\ntext\n{{REAutor|Blub}}", title="RE:Lethaia")
        factory = P921MainSubject(re_page, self.logger)

        # Create an existing (old) P921 claim that points to a redirecting item
        redirect_item = ItemPage(factory.wikidata, "Q6533233")  # -> Q5973878

        # fabricate an old claim list via monkeypatching get_old_claims
        def _make_old_claim():
            claim_json = {
                "mainsnak": {
                    "snaktype": "value",
                    "property": factory.get_property_string(),
                    "datatype": "wikibase-item",
                    "datavalue": {"type": "wikibase-entityid", "value": {"entity-type": "item", "numeric-id": 6533233}}
                },
                "type": "statement",
                "rank": "normal"
            }
            c = pywikibot.Claim.fromJSON(factory.wikidata, claim_json)
            c.setTarget(redirect_item)
            return c

        old_claim = _make_old_claim()
        factory.get_old_claims = lambda _: [old_claim]

        add_remove = factory.get_claims_to_update(ItemPage(factory.wikidata, "Q1234"))

        # Expect: add with resolved target, and remove the original claim
        compare([old_claim], add_remove["remove"])  # remove contains the old redirect claim
        added_claims = add_remove["add"][factory.get_property_string()]
        compare(1, len(added_claims))
        compare("Q5973878", added_claims[0].target.id)

    def test_get_claims_to_update_target_conflict(self):
        re_page = self._create_mock_page(text="{{REDaten|\nWP=de:Aalartige}}\ntext\n{{REAutor|Blub}}", title="RE:Aal")
        factory = P921MainSubject(re_page, self.logger)
        data_item = pywikibot.ItemPage(factory.wikidata, "Q19979634")
        add_remove = factory.get_claims_to_update(data_item)
        compare({'add': {}, 'remove': []}, add_remove)
        compare("[[Kategorie:RE:Wartung Wikidata (WD!=WS)]]", re_page[1]) #  error is persisted in re_page
