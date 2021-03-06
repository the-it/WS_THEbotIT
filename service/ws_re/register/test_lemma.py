# pylint: disable=no-self-use,protected-access
import copy
from collections import OrderedDict
from datetime import datetime

from testfixtures import compare

from service.ws_re.register._base import RegisterException
from service.ws_re.register.authors import Authors
from service.ws_re.register.lemma import Lemma
from service.ws_re.register.lemma_chapter import LemmaChapter
from service.ws_re.register.test_base import BaseTestRegister
from service.ws_re.volumes import Volumes


class TestLemma(BaseTestRegister):
    def setUp(self):
        self.authors = Authors()
        self.volumes = Volumes()
        self.basic_dict = {"lemma": "lemma", "previous": "previous", "next": "next",
                           "redirect": True, "chapters": [{"start": 1, "end": 1, "author": "Herman Abel"},
                                                          {"start": 1, "end": 2, "author": "William Abbott"}]}

    def test_from_dict_errors(self):
        for entry in ["lemma"]:
            test_dict = copy.deepcopy(self.basic_dict)
            del test_dict[entry]
            with self.assertRaises(RegisterException):
                Lemma(test_dict, Volumes()["I,1"], self.authors)

        for entry in ["previous", "next", "redirect", "chapters"]:
            test_dict = copy.deepcopy(self.basic_dict)
            del test_dict[entry]
            self.assertIsNone(Lemma(test_dict, Volumes()["I,1"], self.authors)[entry])

        re_register_lemma = Lemma(self.basic_dict, Volumes()["I,1"], self.authors)
        compare("lemma", re_register_lemma["lemma"])
        compare("previous", re_register_lemma["previous"])
        compare("next", re_register_lemma["next"])
        compare(True, re_register_lemma["redirect"])
        compare([{"start": 1, "end": 1, "author": "Herman Abel"},
                 {"start": 1, "end": 2, "author": "William Abbott"}],
                re_register_lemma["chapters"])
        compare(5, len(re_register_lemma))

    def test_get_link(self):
        re_register_lemma = Lemma(self.basic_dict, self.volumes["I,1"], self.authors)
        compare("[[RE:lemma|''{{Anker2|lemma}}'']]", re_register_lemma.get_link())

        altered_dict = copy.deepcopy(self.basic_dict)
        altered_dict["redirect"] = False
        re_register_lemma = Lemma(altered_dict, self.volumes["I,1"], self.authors)
        compare("[[RE:lemma|'''{{Anker2|lemma}}''']]", re_register_lemma.get_link())

        altered_dict = copy.deepcopy(self.basic_dict)
        altered_dict["redirect"] = "Some other Lemma"
        re_register_lemma = Lemma(altered_dict, self.volumes["I,1"], self.authors)
        compare("[[RE:lemma|''{{Anker2|lemma}}'']] → '''[[RE:Some other Lemma|Some other Lemma]]'''",
                re_register_lemma.get_link())

        altered_dict = copy.deepcopy(self.basic_dict)
        altered_dict["lemma"] = "Ist = gleich"
        re_register_lemma = Lemma(altered_dict, self.volumes["I,1"], self.authors)
        compare("[[RE:Ist = gleich|''{{Anker2|Ist {{=}} gleich}}'']]",
                re_register_lemma.get_link())

    def test_wiki_links(self):
        re_register_lemma = Lemma(self.basic_dict, self.volumes["I,1"], self.authors)
        compare(("", ""), re_register_lemma.get_wiki_links())

        altered_dict = copy.deepcopy(self.basic_dict)
        altered_dict["wp_link"] = "w:de:Lemma"
        re_register_lemma = Lemma(altered_dict, self.volumes["I,1"], self.authors)
        compare(("[[w:de:Lemma|Lemma<sup>(WP de)</sup>]]", "data-sort-value=\"w:de:lemma\""),
                re_register_lemma.get_wiki_links())

        altered_dict = copy.deepcopy(self.basic_dict)
        altered_dict["ws_link"] = "s:de:Lemma"
        re_register_lemma = Lemma(altered_dict, self.volumes["I,1"], self.authors)
        compare(("[[s:de:Lemma|Lemma<sup>(WS de)</sup>]]", "data-sort-value=\"s:de:lemma\""),
                re_register_lemma.get_wiki_links())

        altered_dict = copy.deepcopy(self.basic_dict)
        altered_dict["wd_link"] = "d:Q123456"
        re_register_lemma = Lemma(altered_dict, self.volumes["I,1"], self.authors)
        compare(("[[d:Q123456|WD-Item]]", "data-sort-value=\"d:Q123456\""),
                re_register_lemma.get_wiki_links())

        altered_dict = copy.deepcopy(self.basic_dict)
        altered_dict["wp_link"] = "w:de:Lemma"
        altered_dict["ws_link"] = "s:de:Lemma"
        altered_dict["wd_link"] = "d:Q123456"
        re_register_lemma = Lemma(altered_dict, self.volumes["I,1"], self.authors)
        compare(("[[w:de:Lemma|Lemma<sup>(WP de)</sup>]]<br/>"
                 "[[s:de:Lemma|Lemma<sup>(WS de)</sup>]]<br/>"
                 "[[d:Q123456|WD-Item]]",
                 "data-sort-value=\"w:de:lemma\""),
                re_register_lemma.get_wiki_links())

        altered_dict = copy.deepcopy(self.basic_dict)
        altered_dict["wp_link"] = "w:de:Lemma = Irgendwas"
        re_register_lemma = Lemma(altered_dict, self.volumes["I,1"], self.authors)
        compare(("[[w:de:Lemma = Irgendwas|Lemma {{=}} Irgendwas<sup>(WP de)</sup>]]",
                 "data-sort-value=\"w:de:lemma = irgenduas\""),
                re_register_lemma.get_wiki_links())

    def test_wiki_links_bug_multipart_lemma(self):
        re_register_lemma = Lemma(self.basic_dict, self.volumes["I,1"], self.authors)
        compare(("", ""), re_register_lemma.get_wiki_links())
        altered_dict = copy.deepcopy(self.basic_dict)
        altered_dict["ws_link"] = "s:it:Autore:Lemma"
        altered_dict["wp_link"] = "w:it:Autore:Lemma"
        re_register_lemma = Lemma(altered_dict, self.volumes["I,1"], self.authors)
        compare(("[[w:it:Autore:Lemma|Lemma<sup>(WP it)</sup>]]<br/>"
                 "[[s:it:Autore:Lemma|Lemma<sup>(WS it)</sup>]]",
                 "data-sort-value=\"w:it:autore:lemma\""),
                re_register_lemma.get_wiki_links())

    def test_get_pages(self):
        re_register_lemma = Lemma(self.basic_dict, self.volumes["I,1"], self.authors)
        compare("[[Special:Filepath/Pauly-Wissowa_I,1,_0001.jpg|1]]",
                re_register_lemma._get_pages(LemmaChapter({"start": 1, "end": 1, "author": "Abel"})))
        compare("[[Special:Filepath/Pauly-Wissowa_I,1,_0017.jpg|18]]",
                re_register_lemma._get_pages(LemmaChapter({"start": 18, "author": "Abel"})))
        compare("[[Special:Filepath/Pauly-Wissowa_I,1,_0197.jpg|198]]-200",
                re_register_lemma._get_pages(LemmaChapter({"start": 198, "end": 200, "author": "Abel"})))

    def test_get_author_and_year(self):
        re_register_lemma = Lemma(self.basic_dict, self.volumes["I,1"], self.authors)
        compare("Abert", re_register_lemma._get_author_str(
            LemmaChapter({"start": 1, "end": 2, "author": "Abert"})))
        compare("1927", re_register_lemma._get_death_year(
            LemmaChapter({"start": 1, "end": 2, "author": "Abert"})))
        compare("", re_register_lemma._get_death_year(
            LemmaChapter({"start": 1, "end": 2, "author": "Abbott"})))

        # check use case one chapter several authors
        compare("1998", re_register_lemma._get_death_year(
            LemmaChapter({"start": 1, "end": 2, "author": "redirect_list"})))
        compare("Abert, Herman Abel", re_register_lemma._get_author_str(
            LemmaChapter({"start": 1, "end": 2, "author": "redirect_list"})))

        # check if author not there
        compare("????", re_register_lemma._get_death_year(
            LemmaChapter({"start": 1, "end": 2, "author": "Tada"})))
        compare("Tada", re_register_lemma._get_author_str(
            LemmaChapter({"start": 1, "end": 2, "author": "Tada"})))

        compare("", re_register_lemma._get_death_year(
            LemmaChapter({"start": 1, "end": 2})))
        compare("", re_register_lemma._get_author_str(
            LemmaChapter({"start": 1, "end": 2})))

    def test_year_format(self):
        year_free_content = datetime.now().year - 71
        compare("style=\"background:#B9FFC5\"", Lemma._get_year_format(str(year_free_content)))
        compare("style=\"background:#FFCBCB\"", Lemma._get_year_format(str(year_free_content + 1)))
        compare("style=\"background:#CBCBCB\"", Lemma._get_year_format(""))
        compare("style=\"background:#FFCBCB\"", Lemma._get_year_format("????"))
        compare("style=\"background:#FFCBCB\"", Lemma._get_year_format(None))

    def test_is_valid(self):
        no_chapter_dict = {"lemma": "lemma", "chapters": []}
        Lemma(no_chapter_dict, self.volumes["I,1"], self.authors)
        no_chapter_dict = {"lemma": "lemma", "chapters": [{"end": 1}]}
        with self.assertRaises(RegisterException):
            print(Lemma(no_chapter_dict, self.volumes["I,1"], self.authors))

    def test_get_row(self):
        one_line_dict = {"lemma": "lemma", "previous": "previous", "next": "next",
                         "wp_link": "w:en:Lemma", "ws_link": "s:de:Lemma",
                         "redirect": False, "chapters": [{"start": 1, "end": 1, "author": "Abel"}]}
        re_register_lemma = Lemma(one_line_dict, self.volumes["I,1"], self.authors)
        expected_row = """|-
|data-sort-value="lemma"|[[RE:lemma|'''{{Anker2|lemma}}''']]
|style="background:#AA0000"|UNK
|data-sort-value="w:en:lemma"|[[w:en:Lemma|Lemma<sup>(WP en)</sup>]]<br/>[[s:de:Lemma|Lemma<sup>(WS de)</sup>]]
|[[Special:Filepath/Pauly-Wissowa_I,1,_0001.jpg|1]]
|Herman Abel
|style="background:#FFCBCB"|1998"""
        compare(expected_row, re_register_lemma.get_table_row())
        two_line_dict = {"lemma": "lemma", "previous": "previous", "next": "next",
                         "wp_link": "w:en:Lemm", "ws_link": "s:de:Lemma",
                         "redirect": False, "chapters": [{"start": 1, "end": 1, "author": "Abel"},
                                                         {"start": 1, "end": 4, "author": "Abbott"}]}
        re_register_lemma = Lemma(two_line_dict, self.volumes["I,1"], self.authors)
        expected_row = """|-
|rowspan=2 data-sort-value="lemma"|[[RE:lemma|'''{{Anker2|lemma}}''']]
|rowspan=2 style="background:#AA0000"|UNK
|rowspan=2 data-sort-value="w:en:lemm"|[[w:en:Lemm|Lemm<sup>(WP en)</sup>]]<br/>[[s:de:Lemma|Lemma<sup>(WS de)</sup>]]
|[[Special:Filepath/Pauly-Wissowa_I,1,_0001.jpg|1]]
|Herman Abel
|style="background:#FFCBCB"|1998
|-
|[[Special:Filepath/Pauly-Wissowa_I,1,_0001.jpg|1]]-4
|William Abbott
|style="background:#CBCBCB"|"""
        compare(expected_row, re_register_lemma.get_table_row())
        expected_row = expected_row.replace("data-sort-value=\"lemma\"|[[RE:lemma|'''{{Anker2|lemma}}''']]", "|I,1")
        compare(expected_row, re_register_lemma.get_table_row(print_volume=True))

    def test_get_row_no_chapter(self):
        one_line_dict = {"lemma": "lemma", "previous": "previous", "next": "next",
                         "redirect": False,
                         "chapters": []}
        re_register_lemma = Lemma(one_line_dict, self.volumes["I,1"], self.authors)
        expected_row = """|-
|data-sort-value="lemma"|[[RE:lemma|'''{{Anker2|lemma}}''']]
|style="background:#AA0000"|UNK
||"""
        compare(expected_row, re_register_lemma.get_table_row())

    def test_strip_accents(self):
        compare("Αβαλας λιμηνaoueeeec", Lemma._strip_accents("Ἀβάλας λιμήνäöüèéêëç"))

    def test_sort_key(self):
        compare("uuuiiissceaouesoaceeeeiioouusu", Lemma.make_sort_key("Uv(Wij)'ï?ßçëäöüêśôʾʿâçèéêëîïôöûüśū"))
        compare("flexum", Lemma.make_sort_key("ad Flexum"))
        compare("epistulis", Lemma.make_sort_key("ab epistulis"))
        compare("memoria", Lemma.make_sort_key("a memoria"))
        compare("aabaa abfl", Lemma.make_sort_key("aabaa abfl"))
        compare("aabab abfl", Lemma.make_sort_key("aabab abfl"))
        compare("aabad abfl", Lemma.make_sort_key("aabad abfl"))
        compare("abfl", Lemma.make_sort_key("G. abfl"))
        compare("abdigildus", Lemma.make_sort_key("Abdigildus (?)–-"))
        compare("abd 001 011 230", Lemma.make_sort_key("Abd 1 11 230"))
        compare("e    orceni", Lemma.make_sort_key("E....orceni"))
        compare("abalas limenu", Lemma.make_sort_key("Ἀβάλας λιμήνου"))
        compare("hestiasis", Lemma.make_sort_key("Ἑστίασις"))
        compare("hiaron tas athanaias", Lemma.make_sort_key("Ἱαρὸν τᾶς Ἀθαναίας"))
        compare("agnu keras", Lemma.make_sort_key("Ἀγνοῦ κέρας"))
        compare("aptuchu hieron", Lemma.make_sort_key("Ἀπτούχου ἱερόν"))
        compare("hyakinthis hodos", Lemma.make_sort_key("Ὑακινθὶς ὁδός"))
        compare("kaualenon katoikia", Lemma.make_sort_key("Καυαληνῶν κατοικία"))
        compare("agaua kome", Lemma.make_sort_key("Ἀγαύα κώμη"))
        compare("hyperemeros, hyperemeria", Lemma.make_sort_key("Ὑπερήμερος, ὑπερημερία"))
        compare("he kyria", Lemma.make_sort_key("ἡ κυρία"))
        compare("bokkanon hemeron", Lemma.make_sort_key("Βόκκανον ἥμερον"))
        compare("charisteria eleutherias", Lemma.make_sort_key("Χαριστήρια ἐλευθερίας"))
        compare("ephodion", Lemma.make_sort_key("Ἐφόδιον"))
        compare("alana ore", Lemma.make_sort_key("Ἀλανὰ ὄρη"))
        compare("heraites hormos", Lemma.make_sort_key("Ἡραΐτης Ὅρμος"))
        compare("hamippoi", Lemma.make_sort_key("Ἅμιπποι"))
        compare("chrysun stoma", Lemma.make_sort_key("Χρυσοῦν στόμα"))
        compare("chrysunng stoma", Lemma.make_sort_key("Χρυσοῦνγγ στόμα"))
        # compare("drimylon oros", Lemma.make_sort_key("Δριμύλον ὅρος"))
        compare("hea", Lemma.make_sort_key("Ἑα"))
        compare("ea", Lemma.make_sort_key("Ἐα"))
        compare("iabadiu nesos", Lemma.make_sort_key("Ἰαβαδίου νῆσος"))


    def test_sort_key_provide_by_lemma(self):
        sort_dict = copy.deepcopy(self.basic_dict)
        sort_dict["lemma"] = "Lemma"
        sort_dict["sort_key"] = "WasAnderes"
        sort_lemma = Lemma(sort_dict, self.volumes["I,1"], self.authors)
        compare("uasanderes", sort_lemma.sort_key)

        sort_dict["sort_key"] = "WasAnderes 02"
        sort_lemma = Lemma(sort_dict, self.volumes["I,1"], self.authors)
        compare("uasanderes 002", sort_lemma.sort_key)

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
        dict_lemma = Lemma(reverse_dict, self.volumes["I,1"], self.authors)
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
        compare(expected_dict, dict_lemma.lemma_dict)

        missing_dict = copy.deepcopy(reverse_dict)
        del missing_dict["next"]
        del missing_dict["redirect"]
        missing_dict["previous"] = None
        missing_expected_dict = copy.deepcopy(expected_dict)
        del missing_expected_dict["next"]
        del missing_expected_dict["redirect"]
        del missing_expected_dict["previous"]
        missing_dict_lemma = Lemma(missing_dict, self.volumes["I,1"], self.authors)
        compare(missing_expected_dict, missing_dict_lemma.lemma_dict)

    def test_set_lemma_dict(self):
        update_basic_dict = copy.deepcopy(self.basic_dict)
        update_lemma = Lemma(update_basic_dict, self.volumes["I,1"], self.authors)
        update_dict = {"lemma": "lemma2", "previous": "previous1", "next": "next",
                       "chapters": [{"start": 1, "end": 3, "author": "Abel"},
                                    {"start": 3, "end": 3, "author": "Abbott"}]}
        remove_item = ["redirect", "some_bla"]
        update_lemma.update_lemma_dict(update_dict)
        compare("lemma2", update_lemma["lemma"])
        compare("lemma002", update_lemma.sort_key)
        compare("previous1", update_lemma["previous"])
        compare("next", update_lemma["next"])
        self.assertTrue(update_lemma["redirect"])
        compare([{"start": 1, "end": 3, "author": "Abel"},
                 {"start": 3, "end": 3, "author": "Abbott"}],
                update_lemma.lemma_dict["chapters"])
        update_lemma.update_lemma_dict(update_dict, remove_items=remove_item)
        compare("lemma2", update_lemma["lemma"])
        compare("previous1", update_lemma["previous"])
        compare("next", update_lemma["next"])
        self.assertIsNone(update_lemma["redirect"])
        compare([{"start": 1, "end": 3, "author": "Abel"},
                 {"start": 3, "end": 3, "author": "Abbott"}],
                update_lemma.lemma_dict["chapters"])
