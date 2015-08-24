from unittest import TestCase

__author__ = 'eso'

import sys
sys.path.append('../../')
from tools.template_handler import TemplateHandler

minimal_vorlage_complex = '''{{minimalvorlage
|1=test1
|2=test2
}}'''

minimal_vorlage_simple = '{{minimalvorlage|1=test1|2=test2}}'

without_key = '{{minimalvorlage|test1|2=test2}}'

template_in_template = '{{minimalvorlage|{{otherTemplate|other_argument}}|2=test2}}'

template_in_template_with_key = '{{minimalvorlage|1={{otherTemplate|other_argument}}|2=test2}}'

template_in_template_2 = '{{Sperrsatz|{{Kapitaelchen|Test}}}}'

class TestTemplateHandler(TestCase):
  def test_template_from_page(self):
    handler = TemplateHandler(minimal_vorlage_complex)
    self.assertEqual([{'key': '1', 'value': 'test1'}, {'key': '2', 'value': 'test2'}], handler.get_parameterlist())
    del handler

    handler = TemplateHandler(minimal_vorlage_simple)
    self.assertEqual([{'key': '1', 'value': 'test1'}, {'key': '2', 'value': 'test2'}], handler.get_parameterlist())
    del handler

  def test_get_parameter(self):
      handler = TemplateHandler(minimal_vorlage_simple)
      self.assertEqual({'key': '1', 'value': 'test1'}, handler.get_parameter('1'))
      self.assertEqual({'key': '2', 'value': 'test2'}, handler.get_parameter('2'))

  def test_get_str(self):
      handler = TemplateHandler(minimal_vorlage_simple)
      self.assertEqual('{{minimalvorlage|1=test1|2=test2}}', handler.get_str(str_complex=False))
      self.assertEqual('{{minimalvorlage\n|1=test1\n|2=test2\n}}', handler.get_str(str_complex=True))

  def test_without_key(self):
      handler = TemplateHandler(without_key)
      self.assertEqual('{{minimalvorlage|test1|2=test2}}', handler.get_str(str_complex=False))

  def test_update_parameters(self):
      handler = TemplateHandler(minimal_vorlage_simple)
      self.assertEqual('{{minimalvorlage|1=test1|2=test2}}', handler.get_str(str_complex=False))
      handler.update_parameters([{'key': None, 'value': 'test3'},
                                 {'key': '4', 'value': 'test4'},
                                 {'key': '5', 'value': 'test5'}])
      self.assertEqual('{{minimalvorlage|test3|4=test4|5=test5}}', handler.get_str(str_complex=False))

  def test_template_in_template(self):
      handler = TemplateHandler(template_in_template)
      self.assertListEqual([{'key': None, 'value': '{{otherTemplate|other_argument}}'}, {'key': '2', 'value': 'test2'}],
                           handler.get_parameterlist())
      del handler

      handler = TemplateHandler(template_in_template_with_key)
      self.assertListEqual([{'key': '1', 'value': '{{otherTemplate|other_argument}}'}, {'key': '2', 'value': 'test2'}], 
                           handler.get_parameterlist())
      self.assertListEqual([{'key': '1', 'value': '{{otherTemplate|other_argument}}'}, {'key': '2', 'value': 'test2'}],
                           handler.get_parameterlist())
      del handler

      handler = TemplateHandler(template_in_template_2)
      self.assertListEqual([{'key': None, 'value': '{{Kapitaelchen|Test}}'}], handler.get_parameterlist())

  def test_set_title(self):
      handler = TemplateHandler(minimal_vorlage_simple)
      handler.set_title('testtitle')
      self.assertEqual('{{testtitle|1=test1|2=test2}}', handler.get_str(str_complex=False))