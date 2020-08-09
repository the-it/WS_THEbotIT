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

    def test_index(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Blub}}", title="RE:Register (Band XI)")
        non_claim = NonClaims(re_page).dict
        compare("Index in Paulys Realencyclopädie der classischen Altertumswissenschaft (RE)",
                non_claim["descriptions"]["de"]["value"])
        compare(["de", "en"], non_claim["descriptions"].keys())

    def test_crossref(self):
        re_page = self._create_mock_page(text="{{REDaten|VERWEIS=ON}}\ntext\n{{REAutor|Blub}}", title="RE:BLA")
        non_claim = NonClaims(re_page).dict
        compare("cross-reference en Paulys Realencyclopädie der classischen Altertumswissenschaft (RE)",
                non_claim["descriptions"]["fr"]["value"])
        compare(["de", "da", "el", "en", "es", "fr", "it", "nl", "pt", "sv"], non_claim["descriptions"].keys())

    def test_prologue(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Blub}}", title="RE:Wilhelm Kroll †")
        non_claim = NonClaims(re_page).dict
        compare("prologue in Paulys Realencyclopädie der classischen Altertumswissenschaft (RE)",
                non_claim["descriptions"]["en"]["value"])
        compare(["de", "en"], non_claim["descriptions"].keys())

    def test_badge_fertig(self):
        re_page = self._create_mock_page(text="{{REDaten|KORREKTURSTAND=Fertig}}\ntext\n{{REAutor|Blub}}",
                                         title="RE:Wilhelm Kroll †")
        non_claim = NonClaims(re_page).dict
        compare("Q20748093", non_claim["sitelinks"]["dewikisource"]["badges"][0])

    def test_badge_korrigiert(self):
        re_page = self._create_mock_page(text="{{REDaten|KORREKTURSTAND=Korrigiert}}\ntext\n{{REAutor|Blub}}",
                                         title="RE:Wilhelm Kroll †")
        non_claim = NonClaims(re_page).dict
        compare("Q20748092", non_claim["sitelinks"]["dewikisource"]["badges"][0])

    def test_badge_unkorrigiert(self):
        re_page = self._create_mock_page(text="{{REDaten|KORREKTURSTAND=Unkorrigiert}}\ntext\n{{REAutor|Blub}}",
                                         title="RE:Wilhelm Kroll †")
        non_claim = NonClaims(re_page).dict
        compare("Q20748091", non_claim["sitelinks"]["dewikisource"]["badges"][0])

    def test_labels_and_sitelinks_has_changed_no_change(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Blub}}", title="RE:Wilhelm Kroll †")
        non_claim = NonClaims(re_page)
        old_non_claims = {
            "labels": {
                "de": {
                    "language": "de",
                    "value": "Wilhelm Kroll \u2020 (Pauly-Wissowa)"
                },
                "en": {
                    "language": "en",
                    "value": "Wilhelm Kroll \u2020 (Pauly-Wissowa)"
                }
            },
            "descriptions": {
                "en": {
                    "language": "en",
                    "value": "prologue in Paulys Realencyclop\u00e4die der classischen Altertumswissenschaft (RE)"
                },
                "de": {
                    "language": "de",
                    "value": "Vorwort in Paulys Realencyclop\u00e4die der classischen Altertumswissenschaft (RE)"
                }
            },
            "claims": {
                "P31": [
                    {
                        "mainsnak": {
                            "snaktype": "value",
                            "property": "P31",
                            "datatype": "wikibase-item",
                            "datavalue": {
                                "value": {
                                    "entity-type": "item",
                                    "numeric-id": 920285
                                },
                                "type": "wikibase-entityid"
                            }
                        },
                        "type": "statement",
                        "id": "Q20097915$CA3B6E3A-3963-42F5-936F-DD700D525C4B",
                        "rank": "normal"
                    }
                ]
            },
            "sitelinks": {
                "dewikisource": {
                    "site": "dewikisource",
                    "title": "RE:Wilhelm Kroll \u2020",
                    "badges": []
                }
            }
        }
        compare(False, non_claim.labels_and_sitelinks_has_changed(old_non_claims))

    def test_labels_and_sitelinks_has_changed_nothing_there(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Blub}}", title="RE:Wilhelm Kroll †")
        non_claim = NonClaims(re_page)
        old_non_claims = {}
        compare(True, non_claim.labels_and_sitelinks_has_changed(old_non_claims))

    def test_labels_and_sitelinks_has_changed_more_languages(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Blub}}", title="RE:Wilhelm Kroll †")
        non_claim = NonClaims(re_page)
        old_non_claims = {
            "labels": {
                "de": {
                    "language": "de",
                    "value": "Wilhelm Kroll \u2020 (Pauly-Wissowa)"
                },
                "en": {
                    "language": "en",
                    "value": "Wilhelm Kroll \u2020 (Pauly-Wissowa)"
                },
                "xy": {
                    "language": "xy",
                    "value": "Fantasy Language, shouldn't be a problem"
                }
            },
            "descriptions": {
                "en": {
                    "language": "en",
                    "value": "prologue in Paulys Realencyclop\u00e4die der classischen Altertumswissenschaft (RE)"
                },
                "de": {
                    "language": "de",
                    "value": "Vorwort in Paulys Realencyclop\u00e4die der classischen Altertumswissenschaft (RE)"
                }
            },
            "claims": {
                "P31": [
                    {
                        "mainsnak": {
                            "snaktype": "value",
                            "property": "P31",
                            "datatype": "wikibase-item",
                            "datavalue": {
                                "value": {
                                    "entity-type": "item",
                                    "numeric-id": 920285
                                },
                                "type": "wikibase-entityid"
                            }
                        },
                        "type": "statement",
                        "id": "Q20097915$CA3B6E3A-3963-42F5-936F-DD700D525C4B",
                        "rank": "normal"
                    }
                ]
            },
            "sitelinks": {
                "dewikisource": {
                    "site": "dewikisource",
                    "title": "RE:Wilhelm Kroll \u2020",
                    "badges": []
                }
            }
        }
        compare(False, non_claim.labels_and_sitelinks_has_changed(old_non_claims))
