from unittest import TestCase

__author__ = 'eso'

from tools.date_conversion import DateConversion

class TestDateConversion(TestCase):
  def test__chop_ref(self):
    converter = DateConversion('18. November 1856<ref>something</ref>')
    self.assertEqual('1856-11-18', str(converter))
    del converter

    converter = DateConversion('18. November 1856{{CRef||something}}')
    self.assertEqual('1856-11-18', str(converter))