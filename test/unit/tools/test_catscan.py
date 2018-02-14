import httpretty

from test import *
from tools.catscan import PetScan


class TestCatScan(TestCase):
    def setUp(self):
        self.petscan = PetScan()

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
        self.petscan.add_namespace("Datei")
        self.petscan.add_namespace([2, "Vorlage"])
        self.assertDictEqual({"ns[0]": "1", "ns[2]": "1", "ns[6]": "1", "ns[10]": "1"}, self.petscan.options)

    def test_activate_redirects(self):
        self.petscan.activate_redirects()
        self.assertDictEqual({"show_redirects": "yes"}, self.petscan.options)

    def test_deactivate_redirects(self):
        self.petscan.deactivate_redirects()
        self.assertDictEqual({"show_redirects": "no"}, self.petscan.options)

    def test_last_change_before(self):
        self.petscan.last_change_before(1234, 1, 1, 2, 2, 42)
        self.assertDictEqual({"before": "12340101020242"}, self.petscan.options)

    def test_last_change_after(self):
        self.petscan.last_change_after(1234, 1, 1, 2, 2, 42)
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
        self.petscan.get_pages_with_wikidata_items()
        self.assertDictEqual({"wikidata_item": "with"}, self.petscan.options)

    def test_get_Pages_without_wikidata(self):
        self.petscan.get_pages_without_wikidata_items()
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
        self.assertDictEqual({"edits[bots]": "yes", "edits[anons]": "no", "edits[flagged]": "yes"}, self.petscan.options)

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
        self.petscan.add_yes_template('yes1')
        self.petscan.add_yes_template('yes2')
        self.petscan.add_any_template('any1')
        self.petscan.add_any_template('any2')
        self.petscan.add_any_template('any3')
        self.petscan.add_no_template('no1')
        self.petscan.add_no_template('no2')
        self.assertEqual(str(self.petscan),
                         'https://petscan.wmflabs.org/?language=de&project=wikisource&templates_yes=yes1%0D%0Ayes2&templates_any=any1%0D%0Aany2%0D%0Aany3&templates_no=no1%0D%0Ano2')

    def test_construct_outlinks(self):
        self.petscan.add_yes_outlink('yes1')
        self.petscan.add_yes_outlink('yes2')
        self.petscan.add_any_outlink('any1')
        self.petscan.add_any_outlink('any2')
        self.petscan.add_any_outlink('any3')
        self.petscan.add_no_outlink('no1')
        self.petscan.add_no_outlink('no2')
        self.assertEqual(str(self.petscan),
                         'https://petscan.wmflabs.org/?language=de&project=wikisource&outlinks_yes=yes1%0D%0Ayes2&outlinks_any=any1%0D%0Aany2%0D%0Aany3&outlinks_no=no1%0D%0Ano2')

    def test_construct_links_to(self):
        self.petscan.add_yes_links_to('yes1')
        self.petscan.add_yes_links_to('yes2')
        self.petscan.add_any_links_to('any1')
        self.petscan.add_any_links_to('any2')
        self.petscan.add_any_links_to('any3')
        self.petscan.add_no_links_to('no1')
        self.petscan.add_no_links_to('no2')
        self.assertEqual(str(self.petscan),
                         'https://petscan.wmflabs.org/?language=de&project=wikisource&links_to_all=yes1%0D%0Ayes2&links_to_any=any1%0D%0Aany2%0D%0Aany3&links_to_no=no1%0D%0Ano2')


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
                         'https://petscan.wmflabs.org/?language=en&project=wikipedia&categories=test')
        # only a negative category
        self.petscan.categories = {"positive": [], "negative": []}
        self.petscan.add_negative_category('test')
        self.assertEqual(str(self.petscan),
                         'https://petscan.wmflabs.org/?language=en&project=wikipedia&negcats=test')
        # only a option
        self.petscan.categories = {"positive": [], "negative": []}
        self.petscan.add_options({"max_age": '10'})
        self.assertEqual(str(self.petscan),
                         'https://petscan.wmflabs.org/?language=en&project=wikipedia&max_age=10')

    @httpretty.activate
    def test_do_positive(self):
        httpretty.register_uri(httpretty.GET,
                               'https://petscan.wmflabs.org/'
                               '?language=de'
                               '&project=wikisource'
                               '&categories=Autoren'
                               '&get_q=1'
                               '&show_redirects=no'
                               '&ns[0]=1'
                               '&max_age=4'
                               '8&format=json'
                               '&doit=1',
                               status=200,
                               body='{"n": "result","a": {"querytime_sec": 1.572163,'
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
                                    '"touched": "20161024211701"}]}}]}',
                               content_type='application/json')
        self.assertEqual(self.petscan.run(), [{"id": 3279,
                                               "len": 10197,
                                               "n": "page",
                                               "namespace": 0,
                                               "nstext": "",
                                               "q": "Q60644",
                                               "title": "Friedrich_Rückert",
                                               "touched": "20161024211701"}])

    @httpretty.activate
    def test_do_negative(self):
        httpretty.register_uri(httpretty.GET,
                               'https://petscan.wmflabs.org/'
                               '?language=de'
                               '&project=wikisource'
                               '&categories=Autoren'
                               '&get_q=1'
                               '&show_redirects=no'
                               '&ns[0]=1'
                               '&max_age=48'
                               '&format=json'
                               '&doit=1',
                               status=404)
        with self.assertRaises(ConnectionError):
            self.petscan.run()
