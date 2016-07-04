from unittest import TestCase

__author__ = 'eso'

import sys
sys.path.append('../../')
from tools.template_handler import TemplateHandler

test_title = "vorlage"
test_title_sperr = "Sperrsatz"
test_title_test = "testtitle"

test_string_argument_1 = "1=test1"
test_string_argument_1_no_key = "test1"
test_string_argument_2 = "2=test2"
test_string_argument_3 = "test3"
test_string_argument_4 = "4=test4"
test_string_argument_5 = "5=test5"

test_string_12_complex = "{{" + test_title + "\n|" + test_string_argument_1 + "\n|" + test_string_argument_2 + "\n}}"
test_string_12_simple = "{{" + test_title + "|" + test_string_argument_1 + "|" + test_string_argument_2 + "}}"

test_dict_argument_1 = {"key": '1', "value": 'test1'}
test_dict_argument_1_no_key = {"key": None, "value": 'test1'}
test_dict_argument_2 = {"key": '2', "value": 'test2'}
test_dict_argument_3 = {"key": None, "value": 'test3'}
test_dict_argument_4 = {"key": '4', "value": 'test4'}
test_dict_argument_5 = {"key": '5', "value": 'test5'}

test_list_12 = [test_dict_argument_1, test_dict_argument_2]


class TestTemplateHandler(TestCase):
    def test_template_from_page(self):
        handler = TemplateHandler(test_string_12_complex)
        self.assertEqual(test_list_12, handler.get_parameterlist())

    def test_get_parameter(self):
        handler = TemplateHandler(test_string_12_complex)
        self.assertEqual(test_dict_argument_1, handler.get_parameter('1'))
        self.assertEqual(test_dict_argument_2, handler.get_parameter('2'))

    def test_get_str(self):
        handler = TemplateHandler()
        handler.set_title(test_title)
        handler.update_parameters(test_list_12)
        self.assertEqual(test_string_12_simple, handler.get_str(str_complex=False))
        self.assertEqual(test_string_12_complex, handler.get_str(str_complex=True))

    def test_without_key(self):
        test_string_12_no_key = "{{" + test_title + "|" + test_string_argument_1_no_key + "|" + test_string_argument_2 + "}}"
        test_list_12_no_key = [test_dict_argument_1_no_key, test_dict_argument_2]
        handler = TemplateHandler(test_string_12_no_key)
        self.assertEqual(test_list_12_no_key, handler.get_parameterlist())

    def test_update_parameters(self):
        test_string_345_simple = "{{" + test_title + "|" + test_string_argument_3 + "|" + test_string_argument_4 + "|" + test_string_argument_5 + "}}"
        test_list_345 = [test_dict_argument_3, test_dict_argument_4, test_dict_argument_5]
        handler = TemplateHandler(test_string_12_simple)
        self.assertEqual(test_dict_argument_1, handler.get_parameter('1'))
        self.assertEqual(test_dict_argument_2, handler.get_parameter('2'))
        handler.update_parameters(test_list_345)
        self.assertEqual(test_string_345_simple, handler.get_str(str_complex=False))

    def test_template_in_template(self):
        test_string_argument_template = "{{otherTemplate|other_argument}}"
        test_string_12_template = "{{" + test_title + "|" + test_string_argument_template + "|" + test_string_argument_2 + "}}"
        test_dict_template_no_key = {'key': None, 'value': '{{otherTemplate|other_argument}}'}
        test_list_template_no_key = [test_dict_template_no_key, test_dict_argument_2]
        handler = TemplateHandler(test_string_12_template)
        self.assertListEqual(test_list_template_no_key, handler.get_parameterlist())
        del handler

        test_string_argument_template2 = "{{Kapitaelchen|Test}}"
        test_string_template_2 = "{{" + test_title_sperr + "|" + test_string_argument_template2 + "}}"
        test_dict_template_2 = {'key': None, 'value': '{{Kapitaelchen|Test}}'}
        test_list_template_2 = [test_dict_template_2]
        handler = TemplateHandler(test_string_template_2)
        self.assertListEqual(test_list_template_2, handler.get_parameterlist())
        del handler

        test_string_argument_1_template = "1={{otherTemplate|other_argument}}"
        test_string_12_template_no_key = "{{" + test_title + "|" + test_string_argument_1_template + "|" + test_string_argument_2 + "}}"
        test_dict_template = {'key': '1', 'value': '{{otherTemplate|other_argument}}'}
        test_list_template = [test_dict_template, test_dict_argument_2]
        handler = TemplateHandler(test_string_12_template_no_key)
        self.assertListEqual(test_list_template, handler.get_parameterlist())

    def test_set_title(self):
        test_string_12_test_title = "{{" + test_title_test + "|" + test_string_argument_1 + "|" + test_string_argument_2 + "}}"
        handler = TemplateHandler(test_string_12_simple)
        handler.set_title(test_title_test)
        self.assertEqual(test_string_12_test_title, handler.get_str(str_complex=False))

    def test_link_with_text(self):
        test_string_argument_2_link = "2 = [[link|text for link]] more"
        test_string_12_link = "{{" + test_title + "|" + test_string_argument_1_no_key + "|" + test_string_argument_2_link + "}}"
        test_dict_link = {"key": '2', "value": '[[link|text for link]] more'}
        test_list_link = [test_dict_argument_1_no_key, test_dict_link]
        handler = TemplateHandler(test_string_12_link)
        self.assertEqual(test_list_link, handler.get_parameterlist())

        del handler

        test_string_argument_link = "[[link|text for link]] more"
        test_string_12_link_no_key = "{{" + test_title + "|" + test_string_argument_1_no_key + "|" + test_string_argument_link + "}}"
        test_dict_link_no_key = {"key": None, "value": '[[link|text for link]] more'}
        test_list_link_no_key = [test_dict_argument_1_no_key, test_dict_link_no_key]
        handler = TemplateHandler(test_string_12_link_no_key)
        self.assertEqual(test_list_link_no_key, handler.get_parameterlist())

    def test_second_equal(self):
        test_string_argument_second_equal = "BILD=Der Todesgang des armenischen Volkes.pdf{{!}}page=276"
        test_string_second_equal = "{{" + test_title_test + "|" + test_string_argument_1 + "|" + test_string_argument_second_equal + "}}"
        test_dict_second_equal = {"key": "BILD", "value": 'Der Todesgang des armenischen Volkes.pdf{{!}}page=276'}
        test_list_second_equal = [test_dict_argument_1, test_dict_second_equal]
        handler = TemplateHandler(test_string_second_equal)
        self.assertEqual(test_list_second_equal, handler.get_parameterlist())

    def test_bug_authorlist(self):
        test_string_argument_bug = 'STERBEDATUM = 2. Januar < ref name = "adp" / > oder 31. Januar < ref > 49. Jahres - Bericht d.Schles.Ges.für vaterländische Cultur, S. 317, Nekrolog {{GBS|hP1DAAAAIAAJ|PA317}} < / ref > 1871'
        test_string_bug = "{{" + test_title_test + "|" + test_string_argument_1 + "|" + test_string_argument_bug + "}}"
        test_dict_bug = {"key": "STERBEDATUM", "value": '2. Januar < ref name = "adp" / > oder 31. Januar < ref > 49. Jahres - Bericht d.Schles.Ges.für vaterländische Cultur, S. 317, Nekrolog {{GBS|hP1DAAAAIAAJ|PA317}} < / ref > 1871'}
        test_list_bug = [test_dict_argument_1, test_dict_bug]
        handler = TemplateHandler(test_string_bug)
        real_dict = handler.get_parameterlist()
        self.assertEqual(test_list_bug, real_dict)

        test_string_argument_bug = 'GEBURTSDATUM=1783 < ref name = "EB" >  Encyclopaedia Britannica.  11. Auflage(1911), Bd. 1, S.[[:en:Page:EB1911 - Volume 01. djvu / 792 | 748]] {{an | englisch, im Artikel}} < / ref >'
        test_string_bug = "{{" + test_title_test + "|" + test_string_argument_1 + "|" + test_string_argument_bug + "}}"
        test_dict_bug = {"key": "GEBURTSDATUM", "value": '1783 < ref name = "EB" >  Encyclopaedia Britannica.  11. Auflage(1911), Bd. 1, S.[[:en:Page:EB1911 - Volume 01. djvu / 792 | 748]] {{an | englisch, im Artikel}} < / ref >'}
        test_list_bug = [test_dict_argument_1, test_dict_bug]
        handler = TemplateHandler(test_string_bug)
        real_dict = handler.get_parameterlist()
        self.assertEqual(test_list_bug, real_dict)
