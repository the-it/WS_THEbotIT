# pylint: disable=protected-access,no-self-use
from testfixtures import compare

from service.ws_re.scanner.tasks.wikidata.claims.non_claims import NonClaims
from service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import BaseTestClaimFactory


class TestNonClaims(BaseTestClaimFactory):
    def test_article(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Blub}}", title="RE:Bla")
        non_claim = NonClaims(re_page).dict
        compare("Bla (Pauly-Wissowa)", non_claim["labels"]["de"]["value"])
        compare(["de", "en"], non_claim["labels"].keys())
        compare("encyklopediartikel i Paulys Realencyclopädie der classischen Altertumswissenschaft (RE)",
                non_claim["descriptions"]["sv"]["value"])
        compare(["de", "da", "el", "en", "es", "fr", "it", "nl", "pt", "sv"], non_claim["descriptions"].keys())
        compare({'dewikisource': {'site': 'dewikisource', 'title': 'RE:Bla', 'badges': []}}, non_claim["sitelinks"])
