# pylint: disable=no-self-use,protected-access
import copy
from collections import OrderedDict
from typing import cast

from ddt import file_data, ddt
from testfixtures import compare

from service.ws_re.register._base import RegisterException
from service.ws_re.register.authors import Authors
from service.ws_re.register.lemma import Lemma, LemmaDict, LemmaKeys
from service.ws_re.register.lemma_chapter import LemmaChapter
from service.ws_re.register.test_base import BaseTestRegister
from service.ws_re.volumes import Volumes


@ddt
class TestLemma(BaseTestRegister):
    def setUp(self):
        self.authors = Authors()
        self.volumes = Volumes()
        self.basic_dict: LemmaDict = {"lemma": "lemma", "previous": "previous", "next": "next",
                                      "redirect": True,
                                      "chapters": [{"start": 1, "end": 1, "author": "Herman Abel"},
                                                   {"start": 1, "end": 2, "author": "William Abbott"}]}

    def test_from_dict_errors(self):
        for entry in ["lemma"]:
            test_dict = copy.deepcopy(self.basic_dict)
            del test_dict[cast(LemmaKeys, entry)]
            with self.assertRaises(RegisterException):
                Lemma.from_dict(test_dict, Volumes()["I,1"], self.authors)

        for entry in ["previous", "next", "redirect", "chapters"]:
            test_dict = copy.deepcopy(self.basic_dict)
            del test_dict[cast(LemmaKeys, entry)]
            self.assertIsNone(getattr(Lemma.from_dict(test_dict, Volumes()["I,1"], self.authors), entry))

        re_register_lemma = Lemma.from_dict(self.basic_dict, Volumes()["I,1"], self.authors)
        compare("lemma", re_register_lemma.lemma)
        compare("previous", re_register_lemma.previous)
        compare("next", re_register_lemma.next)
        compare(True, re_register_lemma.redirect)
        compare([{"start": 1, "end": 1, "author": "Herman Abel"},
                 {"start": 1, "end": 2, "author": "William Abbott"}],
                re_register_lemma._get_chapter_dicts())

    def test_get_link(self):
        re_register_lemma = Lemma.from_dict(self.basic_dict, self.volumes["I,1"], self.authors)
        compare("[[RE:lemma|''{{Anker2|lemma}}'']]", re_register_lemma.get_link())

        altered_dict = copy.deepcopy(self.basic_dict)
        altered_dict["redirect"] = False
        re_register_lemma = Lemma.from_dict(altered_dict, self.volumes["I,1"], self.authors)
        compare("[[RE:lemma|'''{{Anker2|lemma}}''']]", re_register_lemma.get_link())

        altered_dict = copy.deepcopy(self.basic_dict)
        altered_dict["redirect"] = "Some other Lemma"
        re_register_lemma = Lemma.from_dict(altered_dict, self.volumes["I,1"], self.authors)
        compare("[[RE:lemma|''{{Anker2|lemma}}'']] → '''[[RE:Some other Lemma|Some other Lemma]]'''",
                re_register_lemma.get_link())

        altered_dict = copy.deepcopy(self.basic_dict)
        altered_dict["lemma"] = "Ist = gleich"
        re_register_lemma = Lemma.from_dict(altered_dict, self.volumes["I,1"], self.authors)
        compare("[[RE:Ist = gleich|''{{Anker2|Ist {{=}} gleich}}'']]",
                re_register_lemma.get_link())

    def test_wiki_links(self):
        re_register_lemma = Lemma.from_dict(self.basic_dict, self.volumes["I,1"], self.authors)
        compare(("", ""), re_register_lemma.get_wiki_links())

        altered_dict = copy.deepcopy(self.basic_dict)
        altered_dict["wp_link"] = "w:de:Lemma"
        re_register_lemma = Lemma.from_dict(altered_dict, self.volumes["I,1"], self.authors)
        compare(("[[w:de:Lemma|Lemma<sup>(WP de)</sup>]]", "data-sort-value=\"w:de:lemma\""),
                re_register_lemma.get_wiki_links())

        altered_dict = copy.deepcopy(self.basic_dict)
        altered_dict["ws_link"] = "s:de:Lemma"
        re_register_lemma = Lemma.from_dict(altered_dict, self.volumes["I,1"], self.authors)
        compare(("[[s:de:Lemma|Lemma<sup>(WS de)</sup>]]", "data-sort-value=\"s:de:lemma\""),
                re_register_lemma.get_wiki_links())

        altered_dict = copy.deepcopy(self.basic_dict)
        altered_dict["wd_link"] = "d:Q123456"
        re_register_lemma = Lemma.from_dict(altered_dict, self.volumes["I,1"], self.authors)
        compare(("[[d:Q123456|WD-Item]]", "data-sort-value=\"d:Q123456\""),
                re_register_lemma.get_wiki_links())

        altered_dict = copy.deepcopy(self.basic_dict)
        altered_dict["wp_link"] = "w:de:Lemma"
        altered_dict["ws_link"] = "s:de:Lemma"
        altered_dict["wd_link"] = "d:Q123456"
        re_register_lemma = Lemma.from_dict(altered_dict, self.volumes["I,1"], self.authors)
        compare(("[[w:de:Lemma|Lemma<sup>(WP de)</sup>]]<br/>"
                 "[[s:de:Lemma|Lemma<sup>(WS de)</sup>]]<br/>"
                 "[[d:Q123456|WD-Item]]",
                 "data-sort-value=\"w:de:lemma\""),
                re_register_lemma.get_wiki_links())

        altered_dict = copy.deepcopy(self.basic_dict)
        altered_dict["wp_link"] = "w:de:Lemma = Irgendwas"
        re_register_lemma = Lemma.from_dict(altered_dict, self.volumes["I,1"], self.authors)
        compare(("[[w:de:Lemma = Irgendwas|Lemma {{=}} Irgendwas<sup>(WP de)</sup>]]",
                 "data-sort-value=\"w:de:lemma = irgenduas\""),
                re_register_lemma.get_wiki_links())

    def test_wiki_links_bug_multipart_lemma(self):
        re_register_lemma = Lemma.from_dict(self.basic_dict, self.volumes["I,1"], self.authors)
        compare(("", ""), re_register_lemma.get_wiki_links())
        altered_dict = copy.deepcopy(self.basic_dict)
        altered_dict["ws_link"] = "s:it:Autore:Lemma"
        altered_dict["wp_link"] = "w:it:Autore:Lemma"
        re_register_lemma = Lemma.from_dict(altered_dict, self.volumes["I,1"], self.authors)
        compare(("[[w:it:Autore:Lemma|Lemma<sup>(WP it)</sup>]]<br/>"
                 "[[s:it:Autore:Lemma|Lemma<sup>(WS it)</sup>]]",
                 "data-sort-value=\"w:it:autore:lemma\""),
                re_register_lemma.get_wiki_links())

    def test_get_pages(self):
        re_register_lemma = Lemma.from_dict(self.basic_dict, self.volumes["I,1"], self.authors)
        compare("[http://elexikon.ch/RE/I,1_1.png 1]",
                re_register_lemma._get_pages(LemmaChapter.from_dict({"start": 1, "end": 1, "author": "Abel"})))
        compare("[http://elexikon.ch/RE/I,1_5.png 3]",
                re_register_lemma._get_pages(LemmaChapter.from_dict({"start": 3, "author": "Abel"})))
        compare("[http://elexikon.ch/RE/I,1_5.png 5]",
                re_register_lemma._get_pages(LemmaChapter.from_dict({"start": 5, "author": "Abel"})))
        compare("[http://elexikon.ch/RE/I,1_17.png 18]",
                re_register_lemma._get_pages(LemmaChapter.from_dict({"start": 18, "author": "Abel"})))
        compare("[http://elexikon.ch/RE/I,1_197.png 198]-200",
                re_register_lemma._get_pages(LemmaChapter.from_dict({"start": 198, "end": 200, "author": "Abel"})))

        re_register_lemma = Lemma.from_dict(self.basic_dict, self.volumes["R"], self.authors)
        compare("[http://elexikon.ch/RE/R_3.png 3]",
                re_register_lemma._get_pages(LemmaChapter.from_dict({"start": 3, "author": "Abel"})))

        re_register_lemma = Lemma.from_dict(self.basic_dict, self.volumes["V A,1"], self.authors)
        compare("[http://elexikon.ch/RE/VA,1_1.png 1]",
                re_register_lemma._get_pages(LemmaChapter.from_dict({"start": 1, "author": "Abel"})))

    #http://elexikon.ch/RE/XVIII,3_289.png
    def test_get_author(self):
        re_register_lemma = Lemma.from_dict(self.basic_dict, self.volumes["I,1"], self.authors)
        compare("Abert", re_register_lemma._get_author_str(
            LemmaChapter.from_dict({"start": 1, "end": 2, "author": "Abert"})))

        # check use case one chapter several authors
        compare("Abert, Herman Abel", re_register_lemma._get_author_str(
            LemmaChapter.from_dict({"start": 1, "end": 2, "author": "redirect_list"})))

        # check if author not there
        compare("Tada", re_register_lemma._get_author_str(
            LemmaChapter.from_dict({"start": 1, "end": 2, "author": "Tada"})))

        compare("", re_register_lemma._get_author_str(
            LemmaChapter.from_dict({"start": 1, "end": 2})))

    def test_get_public_domain_year(self):
        # one author
        small_dict = {"lemma": "lemma", "chapters": [{"start": 1, "end": 1, "author": "Abel"}]}
        re_register_lemma = Lemma.from_dict(small_dict, self.volumes["I,1"], self.authors)
        compare(2069, re_register_lemma._get_public_domain_year())

        # two authors for one article
        small_dict = {"lemma": "lemma", "chapters": [{"start": 1, "end": 1, "author": "redirect_list"}]}
        re_register_lemma = Lemma.from_dict(small_dict, self.volumes["I,1"], self.authors)
        compare(2069, re_register_lemma._get_public_domain_year())

        # two authors two articles
        small_dict = {"lemma": "lemma", "chapters": [{"start": 1, "end": 1, "author": "Abel"},
                                                     {"start": 1, "end": 1, "author": "Abert"}]}
        re_register_lemma = Lemma.from_dict(small_dict, self.volumes["XVI,1"], self.authors)
        compare(2058, re_register_lemma._get_public_domain_year())
        small_dict = {"lemma": "lemma", "chapters": [{"start": 1, "end": 1, "author": "Abert"},
                                                     {"start": 1, "end": 1, "author": "Abel"}]}
        re_register_lemma = Lemma.from_dict(small_dict, self.volumes["XVI,1"], self.authors)
        compare(2058, re_register_lemma._get_public_domain_year())

    @file_data("test_data/test_lemma_status.yml")
    def test_get_lemma_status(self, given, expect):
        small_dict = given
        lemma = Lemma.from_dict(small_dict, Volumes()["I,1"], self.authors)
        compare((expect["label"], expect["color"]), lemma.status)

    def test_is_valid(self):
        no_chapter_dict = {"lemma": "lemma", "chapters": []}
        Lemma.from_dict(no_chapter_dict, self.volumes["I,1"], self.authors)
        no_chapter_dict = {"lemma": "lemma", "chapters": [{"end": 1}]}
        with self.assertRaises(RegisterException):
            print(Lemma.from_dict(no_chapter_dict, self.volumes["I,1"], self.authors))

    def test_get_row(self):
        one_line_dict = {"lemma": "lemma", "previous": "previous", "next": "next", "short_description": "Blub",
                         "wp_link": "w:en:Lemma", "ws_link": "s:de:Lemma",
                         "redirect": False, "chapters": [{"start": 1, "end": 1, "author": "Abel"}]}
        re_register_lemma = Lemma.from_dict(one_line_dict, self.volumes["I,1"], self.authors)
        expected_row = """|-
|[http://elexikon.ch/RE/I,1_1.png 1]
|Herman Abel
|style="background:#FFCBCB"|2069"""
        compare(expected_row, re_register_lemma.get_table_row())
        two_line_dict = {"lemma": "lemma", "previous": "previous", "next": "next", "short_description": "Blub",
                         "wp_link": "w:en:Lemm", "ws_link": "s:de:Lemma",
                         "redirect": False, "chapters": [{"start": 1, "end": 1, "author": "Abel"},
                                                         {"start": 1, "end": 4, "author": "Abbott"}]}
        re_register_lemma = Lemma.from_dict(two_line_dict, self.volumes["I,1"], self.authors)
        expected_row = """|-
|[http://elexikon.ch/RE/I,1_1.png 1]
|Herman Abel
|rowspan=2 style="background:#FFCBCB"|2100
|-
|[http://elexikon.ch/RE/I,1_1.png 1]-4
|William Abbott"""
        compare(expected_row, re_register_lemma.get_table_row())
        expected_row = """|-
|rowspan=2|I,1
|[http://elexikon.ch/RE/I,1_1.png 1]
|Herman Abel
|rowspan=2 style="background:#FFCBCB"|2100
|-
|[http://elexikon.ch/RE/I,1_1.png 1]-4
|William Abbott"""
        compare(expected_row, re_register_lemma.get_table_row(print_volume=True))

    def test_get_row_no_chapter(self):
        one_line_dict = {"lemma": "lemma", "previous": "previous", "next": "next",
                         "redirect": False,
                         "chapters": []}
        re_register_lemma = Lemma.from_dict(one_line_dict, self.volumes["I,1"], self.authors)
        expected_row = """|-
||
||
|style="background:#AA0000"|UNK"""
        compare(expected_row, re_register_lemma.get_table_row())

    def test_strip_accents(self):
        compare("Αβαλας λιμηνaoueeeec", Lemma._strip_accents("Ἀβάλας λιμήνäöüèéêëç"))

    @file_data("test_data/test_lemma_sort_keys.yml")
    def test_sort_key(self, testlist):
        for item in testlist:
            compare(item[1], Lemma.make_sort_key(item[0]))


    def test_sort_key_provide_by_lemma(self):
        sort_dict = copy.deepcopy(self.basic_dict)
        sort_dict["lemma"] = "Lemma"
        sort_dict["sort_key"] = "WasAnderes"
        sort_lemma = Lemma.from_dict(sort_dict, self.volumes["I,1"], self.authors)
        compare("uasanderes", sort_lemma.get_sort_key())

        sort_dict["sort_key"] = "WasAnderes 02"
        sort_lemma = Lemma.from_dict(sort_dict, self.volumes["I,1"], self.authors)
        compare("uasanderes 002", sort_lemma.get_sort_key())

    def test_return_dict(self):
        reverse_dict = {"chapters": [{"start": 1, "author": "Abel", "end": 1},
                                     {"start": 1, "end": 2, "author": "Abbott"}],
                        "wp_link": "tada",
                        "proof_read": 2,
                        "ws_link": "tadü",
                        "sort_key": "something",
                        "redirect": True,
                        "next": "next",
                        "previous": "previous",
                        "lemma": "lemma"}
        dict_lemma = Lemma.from_dict(reverse_dict, self.volumes["I,1"], self.authors)
        chapter_dict_1 = OrderedDict((("start", 1), ("end", 1), ("author", "Abel")))
        chapter_dict_2 = OrderedDict((("start", 1), ("end", 2), ("author", "Abbott")))
        expected_dict = OrderedDict([("lemma", "lemma"),
                                     ("previous", "previous"),
                                     ("next", "next"),
                                     ("sort_key", "something"),
                                     ("redirect", True),
                                     ("proof_read", 2),
                                     ("wp_link", "tada"),
                                     ("ws_link", "tadü"),
                                     ("chapters", [chapter_dict_1, chapter_dict_2])])
        compare(expected_dict, dict_lemma.to_dict())

        missing_dict = copy.deepcopy(reverse_dict)
        del missing_dict["next"]
        del missing_dict["redirect"]
        missing_dict["previous"] = None
        missing_expected_dict = copy.deepcopy(expected_dict)
        del missing_expected_dict["next"]
        del missing_expected_dict["redirect"]
        del missing_expected_dict["previous"]
        missing_dict_lemma = Lemma.from_dict(missing_dict, self.volumes["I,1"], self.authors)
        compare(missing_expected_dict, missing_dict_lemma.to_dict())

    def test_set_lemma_dict(self):
        update_basic_dict = copy.deepcopy(self.basic_dict)
        update_lemma = Lemma.from_dict(update_basic_dict, self.volumes["I,1"], self.authors)
        update_dict = {"lemma": "lemma2", "previous": "previous1", "next": "next",
                       "chapters": [{"start": 1, "end": 3, "author": "Abel"},
                                    {"start": 3, "end": 3, "author": "Abbott"}]}
        remove_item = ["redirect", "some_bla"]
        update_lemma.update_lemma_dict(update_dict)
        compare("lemma2", update_lemma.lemma)
        compare("lemma002", update_lemma.get_sort_key())
        compare("previous1", update_lemma.previous)
        compare("next", update_lemma.next)
        self.assertTrue(update_lemma.redirect)
        compare([{"start": 1, "end": 3, "author": "Abel"},
                 {"start": 3, "end": 3, "author": "Abbott"}],
                update_lemma.to_dict()["chapters"])
        update_lemma.update_lemma_dict(update_dict, remove_items=remove_item)
        compare("lemma2", update_lemma.lemma)
        compare("previous1", update_lemma.previous)
        compare("next", update_lemma.next)
        self.assertIsNone(update_lemma.redirect)
        compare([{"start": 1, "end": 3, "author": "Abel"},
                 {"start": 3, "end": 3, "author": "Abbott"}],
                update_lemma.to_dict()["chapters"])

    @file_data("test_data/test_lemma_exists.yml")
    def test_exists(self, given, expect):
        lemma = Lemma(**given, volume=self.volumes["I,1"], authors=self.authors)
        compare(expect, lemma.exists)
