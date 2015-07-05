from unittest import TestCase
import httpretty

__author__ = 'eso'

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

    def test_contruct_cat_string(self):
        self.catscan.add_positive_category("pos1")
        self.catscan.add_positive_category("pos2")
        self.catscan.add_negative_category("neg1")
        self.catscan.add_negative_category("neg2")
        self.catscan.add_negative_category("neg3")
        self.assertEqual("pos1%0D%0Apos2", self.catscan._construct_cat_string(self.catscan.categories["positive"]))
        self.assertEqual("neg1%0D%0Aneg2%0D%0Aneg3", self.catscan._construct_cat_string(self.catscan.categories["negative"]))

    def test_construct_options(self):
        self.catscan._options = {"max_age": "1234",
                                 "get_q": "1",
                                 "show_redirects": "yes"}
        self.assertEqual("&max_age=1234" in "&max_age=1234&get_q=1&show_redirects=yes", True)
        self.assertEqual("&get_q=1" in "&max_age=1234&get_q=1&show_redirects=yes", True)
        self.assertEqual("&show_redirects=yes" in "&max_age=1234&get_q=1&show_redirects=yes", True)

    @httpretty.activate
    def test_do_positive(self):
        httpretty.register_uri(httpretty.GET, 'http://tools.wmflabs.org/catscan2/catscan2.php?language=de&project=wikisource&categories=Autoren&get_q=1&show_redirects=no&ns[0]=1&max_age=48&format=json&doit=1',
                               status=200,
                               body='{"n":"result","a":{"querytime_sec":0.65997004508972},"*":[{"n":"combination","a":{"type":"subset","*":[{"n":"page","a":{"title":"Adam_Wolf","id":"26159","namespace":"0","len":"2122","touched":"20150702080634","q":"Q6245809","nstext":"(Article)"}},{"n":"page","a":{"title":"Victoria","id":"393175","namespace":"0","len":"1677","touched":"20150702092244","q":"Q9439","nstext":"(Article)"}}]}}]}',
                               content_type='application/json')
        self.assertEqual(self.catscan.run(), [{"n":"page","a":{"title":"Adam_Wolf","id":"26159","namespace":"0","len":"2122","touched":"20150702080634","q":"Q6245809","nstext":"(Article)"}},{"n":"page","a":{"title":"Victoria","id":"393175","namespace":"0","len":"1677","touched":"20150702092244","q":"Q9439","nstext":"(Article)"}}])

    @httpretty.activate
    def test_do_negative(self):
        httpretty.register_uri(httpretty.GET, 'http://tools.wmflabs.org/catscan2/catscan2.php?language=de&project=wikisource&categories=Autoren&get_q=1&show_redirects=no&ns[0]=1&max_age=48&format=json&doit=1',
                               status=404)
        self.assertRaises(ConnectionError)
