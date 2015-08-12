__author__ = 'Erik Sommer'

import sys
sys.path.append('../../')
from unittest import TestCase
import httpretty
from tools.catscan import CatScan


class TestCatScan(TestCase):
    def setUp(self):
        self.catscan = CatScan()

    def test_add_options(self):
        self.catscan.add_options({"max_age": "45"})
        self.catscan.add_options({"smaller": "300"})
        self.assertDictEqual({"smaller": "300", "max_age": "45"}, self.catscan._options)

    def test_add_categoy(self):
        self.catscan.add_positive_category("pos1")
        self.catscan.add_positive_category("pos2")
        self.catscan.add_negative_category("neg1")
        self.catscan.add_negative_category("neg2")
        self.assertEqual(["pos1", "pos2"], self.catscan.categories["positive"])
        self.assertEqual(["neg1", "neg2"], self.catscan.categories["negative"])

    def test_add_namespace(self):
        self.catscan.add_namespace(0)
        self.catscan.add_namespace("Datei")
        self.catscan.add_namespace([2, "Vorlage"])
        self.assertDictEqual({"ns[0]": "1", "ns[2]": "1", "ns[6]": "1", "ns[10]": "1"}, self.catscan._options)

    def test_activate_redirects(self):
        self.catscan.activate_redirects()
        self.assertDictEqual({"show_redirects": "yes"}, self.catscan._options)

    def test_deactivate_redirects(self):
        self.catscan.deactivate_redirects()
        self.assertDictEqual({"show_redirects": "no"}, self.catscan._options)

    def test_last_change_before(self):
        self.catscan.last_change_before(1234, 1, 1, 2, 2, 42)
        self.assertDictEqual({"before": "12340101020242"}, self.catscan._options)

    def test_last_change_after(self):
        self.catscan.last_change_after(1234, 1, 1, 2, 2, 42)
        self.assertDictEqual({"after": "12340101020242"}, self.catscan._options)

    def test_max_age(self):
        self.catscan.max_age(1234)
        self.assertDictEqual({"max_age": "1234"}, self.catscan._options)

    def test_only_new(self):
        self.catscan.only_new()
        self.assertDictEqual({"only_new": "1"}, self.catscan._options)

    def test_smaller_then(self):
        self.catscan.smaller_then(42)
        self.assertDictEqual({"smaller": "42"}, self.catscan._options)

    def test_larger_then(self):
        self.catscan.larger_then(42)
        self.assertDictEqual({"larger": "42"}, self.catscan._options)

    def test_get_wikidata(self):
        self.catscan.get_wikidata()
        self.assertDictEqual({"get_q": "1"}, self.catscan._options)

    def test_set_logic_complete(self):
        self.catscan.set_logic(log_and = True, log_or = True)
        self.assertDictEqual({"comb[subset]": "1", "comb[union]": "1"}, self.catscan._options)

    def test_set_logic_only_and(self):
        self.catscan.set_logic(log_and = True)
        self.assertDictEqual({}, self.catscan._options)

    def test_set_logic_only_or(self):
        self.catscan.set_logic(log_or = True)
        self.assertDictEqual({"comb[union]": "1"}, self.catscan._options)

    def test_contruct_cat_string(self):
        self.catscan.add_positive_category("pos 1")
        self.catscan.add_positive_category("pos2")
        self.catscan.add_negative_category("neg1")
        self.catscan.add_negative_category("neg 2")
        self.catscan.add_negative_category("neg3")
        self.assertEqual("pos+1%0D%0Apos2", self.catscan._construct_cat_string(self.catscan.categories["positive"]))
        self.assertEqual("neg1%0D%0Aneg+2%0D%0Aneg3",
                         self.catscan._construct_cat_string(self.catscan.categories["negative"]))

    def test_construct_templates(self):
        self.catscan.add_yes_template('yes1')
        self.catscan.add_yes_template('yes2')
        self.catscan.add_any_template('any1')
        self.catscan.add_any_template('any2')
        self.catscan.add_any_template('any3')
        self.catscan.add_no_template('no1')
        self.catscan.add_no_template('no2')
        self.assertEqual(str(self.catscan),
                         'http://tools.wmflabs.org/catscan2/catscan2.php?language=de&project=wikisource&templates_yes=yes1%0D%0Ayes2&templates_any=any1%0D%0Aany2%0D%0Aany3&templates_no=no1%0D%0Ano2&format=json&doit=1')

    def test_construct_outlinks(self):
        self.catscan.add_yes_outlink('yes1')
        self.catscan.add_yes_outlink('yes2')
        self.catscan.add_any_outlink('any1')
        self.catscan.add_any_outlink('any2')
        self.catscan.add_any_outlink('any3')
        self.catscan.add_no_outlink('no1')
        self.catscan.add_no_outlink('no2')
        self.assertEqual(str(self.catscan),
                         'http://tools.wmflabs.org/catscan2/catscan2.php?language=de&project=wikisource&outlinks_yes=yes1%0D%0Ayes2&outlinks_any=any1%0D%0Aany2%0D%0Aany3&outlinks_no=no1%0D%0Ano2&format=json&doit=1')


    def test_construct_options(self):
        self.catscan._options = {"max_age": "1234",
                                 "get_q": "1",
                                 "show_redirects": "yes"}
        self.assertEqual("&max_age=1234" in str(self.catscan), True)
        self.assertEqual("&get_q=1" in str(self.catscan), True)
        self.assertEqual("&show_redirects=yes" in str(self.catscan), True)

    def test_construct_string(self):
        self.catscan.set_language("en")
        self.catscan.set_project("wikipedia")
        # only a positive category
        self.catscan.add_positive_category("test")
        self.assertEqual(str(self.catscan),
                         'http://tools.wmflabs.org/catscan2/catscan2.php?language=en&project=wikipedia&categories=test&format=json&doit=1')
        # only a negative category
        self.catscan.categories = {"positive": [], "negative": []}
        self.catscan.add_negative_category('test')
        self.assertEqual(str(self.catscan),
                         'http://tools.wmflabs.org/catscan2/catscan2.php?language=en&project=wikipedia&negcats=test&format=json&doit=1')
        # only a option
        self.catscan.categories = {"positive": [], "negative": []}
        self.catscan.add_options({"max_age": '10'})
        self.assertEqual(str(self.catscan),
                         'http://tools.wmflabs.org/catscan2/catscan2.php?language=en&project=wikipedia&max_age=10&format=json&doit=1')

    @httpretty.activate
    def test_do_positive(self):
        httpretty.register_uri(httpretty.GET,
                               'http://tools.wmflabs.org/catscan2/catscan2.php?language=de&project=wikisource&categories=Autoren&get_q=1&show_redirects=no&ns[0]=1&max_age=48&format=json&doit=1',
                               status=200,
                               body='{"n":"result","a":{"querytime_sec":0.65997004508972},"*":[{"n":"combination","a":{"type":"subset","*":[{"n":"page","a":{"title":"Adam_Wolf","id":"26159","namespace":"0","len":"2122","touched":"20150702080634","q":"Q6245809","nstext":"(Article)"}},{"n":"page","a":{"title":"Victoria","id":"393175","namespace":"0","len":"1677","touched":"20150702092244","q":"Q9439","nstext":"(Article)"}}]}}]}',
                               content_type='application/json')
        self.assertEqual(self.catscan.run(), [{"n": "page", "a": {"title": "Adam_Wolf", "id": "26159", "namespace": "0",
                                                                  "len": "2122", "touched": "20150702080634",
                                                                  "q": "Q6245809", "nstext": "(Article)"}},
                                              {"n": "page", "a": {"title": "Victoria", "id": "393175", "namespace": "0",
                                                                  "len": "1677", "touched": "20150702092244",
                                                                  "q": "Q9439", "nstext": "(Article)"}}])

    @httpretty.activate
    def test_do_negative(self):
        httpretty.register_uri(httpretty.GET,
                               'http://tools.wmflabs.org/catscan2/catscan2.php?language=de&project=wikisource&categories=Autoren&get_q=1&show_redirects=no&ns[0]=1&max_age=48&format=json&doit=1',
                               status=404)
        self.assertRaises(ConnectionError)
