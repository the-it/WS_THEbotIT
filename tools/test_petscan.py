# pylint: disable=protected-access
from datetime import datetime
from unittest import TestCase, mock
from unittest.mock import patch

import requests_mock
from freezegun import freeze_time
from testfixtures import compare

from tools.petscan import PetScan, PetScanException, get_processed_time


class TestPetScan(TestCase):
    def setUp(self):
        self.petscan = PetScan()

    def tearDown(self):
        mock.patch.stopall()

    def test_add_options(self):
        self.petscan.add_options({"max_age": "45"})
        self.petscan.add_options({"smaller": "300"})
        self.assertDictEqual({"smaller": "300", "max_age": "45"}, self.petscan.options)

    def test_add_categoy(self):
        self.petscan.add_positive_category("pos1")
        self.petscan.add_positive_category("pos2")
        self.petscan.add_positive_category("pos3", 2)
        self.petscan.add_negative_category("neg1")
        self.petscan.add_negative_category("neg2")
        self.petscan.add_negative_category("neg3", 3)
        self.assertEqual(["pos1", "pos2", "pos3|2"], self.petscan.categories["positive"])
        self.assertEqual(["neg1", "neg2", "neg3|3"], self.petscan.categories["negative"])

    def test_add_namespace(self):
        self.petscan.add_namespace(0)
        self.petscan.add_namespace([2, 10])
        self.assertDictEqual({"ns[0]": "1", "ns[2]": "1", "ns[10]": "1"}, self.petscan.options)

    def test_add_namespace_strings(self):
        self.petscan.add_namespace("Seite")
        self.petscan.add_namespace(["Vorlage", "Hilfe"])
        self.assertDictEqual({"ns[102]": "1", "ns[10]": "1", "ns[12]": "1"}, self.petscan.options)

    def test_activate_redirects(self):
        self.petscan.activate_redirects()
        self.assertDictEqual({"show_redirects": "yes"}, self.petscan.options)

    def test_deactivate_redirects(self):
        self.petscan.deactivate_redirects()
        self.assertDictEqual({"show_redirects": "no"}, self.petscan.options)

    def test_last_change_before(self):
        self.petscan.last_change_before(datetime(year=1234, month=1, day=1, hour=2, minute=2, second=42))
        self.assertDictEqual({"before": "12340101020242"}, self.petscan.options)

    def test_last_change_after(self):
        self.petscan.last_change_after(datetime(year=1234, month=1, day=1, hour=2, minute=2, second=42))
        self.assertDictEqual({"after": "12340101020242"}, self.petscan.options)

    def test_max_age(self):
        self.petscan.max_age(1234)
        self.assertDictEqual({"max_age": "1234"}, self.petscan.options)

    def test_only_new(self):
        self.petscan.only_new()
        self.assertDictEqual({"only_new": "1"}, self.petscan.options)

    def test_smaller_then(self):
        self.petscan.smaller_then(42)
        self.assertDictEqual({"smaller": "42"}, self.petscan.options)

    def test_larger_then(self):
        self.petscan.larger_then(42)
        self.assertDictEqual({"larger": "42"}, self.petscan.options)

    def test_get_wikidata(self):
        self.petscan.get_wikidata_items()
        self.assertDictEqual({"wikidata_item": "any"}, self.petscan.options)

    def test_get_Pages_with_wikidata(self):
        self.petscan.get_pages_with_wd_items()
        self.assertDictEqual({"wikidata_item": "with"}, self.petscan.options)

    def test_get_Pages_without_wikidata(self):
        self.petscan.get_pages_without_wd_items()
        self.assertDictEqual({"wikidata_item": "without"}, self.petscan.options)

    def test_set_or(self):
        self.petscan.set_logic_union()
        self.assertDictEqual({"combination": "union"}, self.petscan.options)

    def test_set_regex(self):
        self.petscan.set_regex_filter("abc")
        self.assertDictEqual({"regexp_filter": "abc"}, self.petscan.options)

    def test_set_last_edits(self):
        self.petscan.set_last_edit_bots(True)
        self.petscan.set_last_edit_anons(False)
        self.petscan.set_last_edit_flagged()
        self.assertDictEqual({"edits[bots]": "yes", "edits[anons]": "no", "edits[flagged]": "yes"},
                             self.petscan.options)

    def test_construct_cat_string(self):
        self.petscan.add_positive_category("pos 1")
        self.petscan.add_positive_category("pos2")
        self.petscan.add_negative_category("neg1")
        self.petscan.add_negative_category("neg 2")
        self.petscan.add_negative_category("neg3")
        self.assertEqual("pos+1\r\npos2", self.petscan._construct_list_argument(self.petscan.categories["positive"]))
        self.assertEqual("neg1\r\nneg+2\r\nneg3",
                         self.petscan._construct_list_argument(self.petscan.categories["negative"]))

    def test_construct_templates(self):
        self.petscan.add_yes_template("yes1")
        self.petscan.add_yes_template("yes2")
        self.petscan.add_any_template("any1")
        self.petscan.add_any_template("any2")
        self.petscan.add_any_template("any3")
        self.petscan.add_no_template("no1")
        self.petscan.add_no_template("no2")
        self.assertEqual(str(self.petscan),
                         "https://petscan.wmflabs.org/?language=de"
                         "&project=wikisource"
                         "&templates_yes=yes1%0D%0Ayes2"
                         "&templates_any=any1%0D%0Aany2%0D%0Aany3"
                         "&templates_no=no1%0D%0Ano2")

    def test_construct_outlinks(self):
        self.petscan.add_yes_outlink("yes1")
        self.petscan.add_yes_outlink("yes2")
        self.petscan.add_any_outlink("any1")
        self.petscan.add_any_outlink("any2")
        self.petscan.add_any_outlink("any3")
        self.petscan.add_no_outlink("no1")
        self.petscan.add_no_outlink("no2")
        self.assertEqual(str(self.petscan),
                         "https://petscan.wmflabs.org/?language=de"
                         "&project=wikisource"
                         "&outlinks_yes=yes1%0D%0Ayes2"
                         "&outlinks_any=any1%0D%0Aany2%0D%0Aany3"
                         "&outlinks_no=no1%0D%0Ano2")

    def test_construct_links_to(self):
        self.petscan.add_yes_links_to("yes1")
        self.petscan.add_yes_links_to("yes2")
        self.petscan.add_any_links_to("any1")
        self.petscan.add_any_links_to("any2")
        self.petscan.add_any_links_to("any3")
        self.petscan.add_no_links_to("no1")
        self.petscan.add_no_links_to("no2")
        self.assertEqual(str(self.petscan),
                         "https://petscan.wmflabs.org/?language=de"
                         "&project=wikisource"
                         "&links_to_all=yes1%0D%0Ayes2"
                         "&links_to_any=any1%0D%0Aany2%0D%0Aany3"
                         "&links_to_no=no1%0D%0Ano2")

    def test_construct_options(self):
        self.petscan.options = {"max_age": "1234",
                                "get_q": "1",
                                "show_redirects": "yes"}
        self.assertEqual("&max_age=1234" in str(self.petscan), True)
        self.assertEqual("&get_q=1" in str(self.petscan), True)
        self.assertEqual("&show_redirects=yes" in str(self.petscan), True)

    def test_construct_string(self):
        self.petscan.set_language("en")
        self.petscan.set_project("wikipedia")
        # only a positive category
        self.petscan.add_positive_category("test")
        self.assertEqual(str(self.petscan),
                         "https://petscan.wmflabs.org/?language=en&project=wikipedia&categories=test")
        # only a negative category
        self.petscan.categories = {"positive": [], "negative": []}
        self.petscan.add_negative_category("test")
        self.assertEqual(str(self.petscan),
                         "https://petscan.wmflabs.org/?language=en&project=wikipedia&negcats=test")
        # only a option
        self.petscan.categories = {"positive": [], "negative": []}
        self.petscan.add_options({"max_age": "10"})
        self.assertEqual(str(self.petscan),
                         "https://petscan.wmflabs.org/?language=en&project=wikipedia&max_age=10")

    def test_do_positive(self):
        with requests_mock.mock() as request_mock:
            request_mock.get("https://petscan.wmflabs.org/"
                             "?language=de&project=wikisource&format=json&doit=1",
                             text='{"n": "result","a": {"querytime_sec": 1.572163,'
                                  '"query": "https://petscan.wmflabs.org/?language=de'
                                  '&project=wikisource&categories=Autoren&get_q=1'
                                  '&show_redirects=no&ns[0]=1&max_age=48'
                                  '&format=json&doit=1"},'
                                  '"*": [{"n": "combination",'
                                  '"a": {"type": "subset",'
                                  '"*": [{"id": 3279,'
                                  '"len": 10197,'
                                  '"n": "page",'
                                  '"namespace": 0,'
                                  '"nstext": "",'
                                  '"q": "Q60644",'
                                  '"title": "Friedrich_Rückert",'
                                  '"touched": "20161024211701"}]}}]}')
            self.assertEqual(self.petscan.run(), [{"id": 3279,
                                                   "len": 10197,
                                                   "n": "page",
                                                   "namespace": 0,
                                                   "nstext": "",
                                                   "q": "Q60644",
                                                   "title": "Friedrich_Rückert",
                                                   "touched": "20161024211701"}])

    def test_do_negative(self):
        with requests_mock.mock() as request_mock:
            request_mock.get("https://petscan.wmflabs.org/"
                             "?language=de&project=wikisource&format=json&doit=1",
                             status_code=404)
            with self.assertRaises(PetScanException):
                self.petscan.run()

    @freeze_time("2000-12-31", auto_tick_seconds=60)
    def test_third_try(self):
        with patch('time.sleep', return_value=None) as sleep_mock:
            with requests_mock.mock() as request_mock:
                request_mock.get("https://petscan.wmflabs.org/"
                                 "?language=de&project=wikisource&format=json&doit=1",
                                 [
                                     {"status_code": 200,
                                      "text": '{"n": "result","a": {"querytime_sec": 1.572163,'
                                              '"query": "https://petscan.wmflabs.org/?language=de'
                                              '&project=wikisource&categories=Autoren&get_q=1'
                                              '&show_redirects=no&ns[0]=1&max_age=48'
                                              '&format=json&doit=1"}}'},
                                     {"status_code": 200,
                                      "text": '{"n": "result","a": {"querytime_sec": 1.572163,'
                                              '"query": "https://petscan.wmflabs.org/?language=de'
                                              '&project=wikisource&categories=Autoren&get_q=1'
                                              '&show_redirects=no&ns[0]=1&max_age=48'
                                              '&format=json&doit=1"}}'},
                                     {"status_code": 200,
                                      "text": '{"n": "result","a": {"querytime_sec": 1.572163,'
                                              '"query": "https://petscan.wmflabs.org/?language=de'
                                              '&project=wikisource&categories=Autoren&get_q=1'
                                              '&show_redirects=no&ns[0]=1&max_age=48'
                                              '&format=json&doit=1"},'
                                              '"*": [{"n": "combination",'
                                              '"a": {"type": "subset",'
                                              '"*": [{"id": 3279,'
                                              '"len": 10197,'
                                              '"n": "page",'
                                              '"namespace": 0,'
                                              '"nstext": "",'
                                              '"q": "Q60644",'
                                              '"title": "Friedrich_Rückert",'
                                              '"touched": "20161024211701"}]}}]}'}
                                 ]
                                 )
                self.assertEqual(self.petscan.run(), [{"id": 3279,
                                                       "len": 10197,
                                                       "n": "page",
                                                       "namespace": 0,
                                                       "nstext": "",
                                                       "q": "Q60644",
                                                       "title": "Friedrich_Rückert",
                                                       "touched": "20161024211701"}])
                compare(2, sleep_mock.call_count)

    @freeze_time("2000-12-31", auto_tick_seconds=60)
    def test_timeout(self):
        with patch('time.sleep', return_value=None) as sleep_mock:
            with requests_mock.mock() as request_mock:
                request_mock.get("https://petscan.wmflabs.org/"
                                 "?language=de&project=wikisource&format=json&doit=1",
                                 text='{"n": "result","a": {"querytime_sec": 1.572163,'
                                      '"query": "https://petscan.wmflabs.org/?language=de'
                                      '&project=wikisource&categories=Autoren&get_q=1'
                                      '&show_redirects=no&ns[0]=1&max_age=48'
                                      '&format=json&doit=1"}}',
                                 status_code=200)
                with self.assertRaises(PetScanException):
                    self.petscan.run()
                compare(5, sleep_mock.call_count)

    result_of_searcher = [{"id": 42, "len": 42, "n": "page", "namespace": 0, "nstext": '',
                           "title": "RE:Lemma1", "touched": "20010101232359"},
                          {"id": 42, "len": 42, "n": "page", "namespace": 0, "nstext": '',
                           "title": "RE:Lemma2", "touched": "20000101232359"},
                          {"id": 42, "len": 42, "n": "page", "namespace": 0, "nstext": '',
                           "title": "RE:Lemma3", "touched": "19990101232359"}
                          ]

    result_of_searcher_max_age = [{"id": 42, "len": 42, "n": "page", "namespace": 0, "nstext": '',
                                   "title": "RE:Lemma4", "touched": "20010101232359"},
                                  ]

    def mock_searcher(self):
        petscan_patcher = mock.patch("tools.petscan.PetScan.run")  # pylint: disable=attribute-defined-outside-init)
        petscan_mock = petscan_patcher.start()  # pylint: disable=attribute-defined-outside-init)
        self.addCleanup(mock.patch.stopall)
        return petscan_mock

    def test_get_combined_lemmas_no_old_lemmas(self):
        petscan_mock = self.mock_searcher()
        petscan_mock.return_value = self.result_of_searcher
        compare(([":RE:Lemma1", ":RE:Lemma2", ":RE:Lemma3"], 3), self.petscan.get_combined_lemma_list({}))

    def test_get_combined_lemmas_old_lemmas(self):
        petscan_mock = self.mock_searcher()
        petscan_mock.return_value = self.result_of_searcher
        compare(([":RE:Lemma2", ":RE:Lemma3", ":RE:Lemma1"], 2),
                self.petscan.get_combined_lemma_list({":RE:Lemma1": "20010101232359"}))
        compare(([":RE:Lemma2", ":RE:Lemma1", ":RE:Lemma3"], 1),
                self.petscan.get_combined_lemma_list({":RE:Lemma1": "20010101232359", ":RE:Lemma3": "20020101232359"}))

    def test_get_combined_with_max_age(self):
        petscan_mock = self.mock_searcher()
        petscan_mock.side_effect = [self.result_of_searcher, self.result_of_searcher_max_age]
        compare(([":RE:Lemma4", ":RE:Lemma1", ":RE:Lemma2", ":RE:Lemma3"], 4),
                self.petscan.get_combined_lemma_list({}, timeframe=42))
        petscan_mock.side_effect = [self.result_of_searcher, self.result_of_searcher_max_age]
        compare(([":RE:Lemma4", ":RE:Lemma2", ":RE:Lemma3", ":RE:Lemma1"], 3),
                self.petscan.get_combined_lemma_list({":RE:Lemma1": "20010101232359"}, timeframe=42))

    @staticmethod
    @freeze_time("2001-12-31")
    def test_get_processed_time():
        compare("20011231000000", get_processed_time())
